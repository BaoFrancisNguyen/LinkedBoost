# models/simple_search.py - Moteur de recherche TF-IDF simple
import sqlite3
import json
import re
from typing import List, Dict, Any
from collections import Counter
import math
import logging

logger = logging.getLogger(__name__)

class SimpleSearchEngine:
    """Moteur de recherche basé sur TF-IDF sans dépendances externes"""
    
    def __init__(self):
        self.db_path = "data/simple_search.db"
        self.create_search_tables()
    
    def create_search_tables(self):
        """Crée les tables pour l'indexation TF-IDF"""
        import os
        os.makedirs("data", exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table des documents (offres d'emploi)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hash_id TEXT UNIQUE,
                content TEXT,
                word_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table des termes et leurs fréquences
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS term_frequencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                term TEXT,
                frequency INTEGER,
                tf_score REAL,
                FOREIGN KEY (document_id) REFERENCES documents (id)
            )
        ''')
        
        # Index pour améliorer les performances
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_term 
            ON term_frequencies(term)
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Tables TF-IDF créées")
    
    def store_job(self, job_data: Dict[str, Any]) -> bool:
        """Indexe une offre d'emploi"""
        try:
            # Construction du contenu textuel
            content = self.build_job_content(job_data)
            hash_id = job_data.get('hash_id', self.generate_hash(content))
            
            # Tokenisation et nettoyage
            tokens = self.tokenize(content)
            word_count = len(tokens)
            
            # Calcul des fréquences
            term_frequencies = Counter(tokens)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Vérifier si déjà indexé
            cursor.execute('SELECT id FROM documents WHERE hash_id = ?', (hash_id,))
            existing = cursor.fetchone()
            
            if existing:
                return False  # Déjà indexé
            
            # Insérer le document
            cursor.execute('''
                INSERT INTO documents (hash_id, content, word_count)
                VALUES (?, ?, ?)
            ''', (hash_id, content, word_count))
            
            document_id = cursor.lastrowid
            
            # Insérer les fréquences des termes
            for term, frequency in term_frequencies.items():
                tf_score = frequency / word_count if word_count > 0 else 0
                
                cursor.execute('''
                    INSERT INTO term_frequencies (document_id, term, frequency, tf_score)
                    VALUES (?, ?, ?, ?)
                ''', (document_id, term, frequency, tf_score))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"✅ Offre indexée: {job_data.get('title', 'Sans titre')}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur indexation: {e}")
            return False
    
    def search_jobs(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Recherche par score TF-IDF"""
        try:
            # Tokenisation de la requête
            query_terms = self.tokenize(query)
            
            if not query_terms:
                return []
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calcul du nombre total de documents
            cursor.execute('SELECT COUNT(*) FROM documents')
            total_docs = cursor.fetchone()[0]
            
            if total_docs == 0:
                conn.close()
                return []
            
            # Calcul des scores TF-IDF pour chaque document
            document_scores = {}
            
            for term in query_terms:
                # Nombre de documents contenant ce terme (DF)
                cursor.execute('''
                    SELECT COUNT(DISTINCT document_id) 
                    FROM term_frequencies 
                    WHERE term = ?
                ''', (term,))
                
                df = cursor.fetchone()[0]
                
                if df == 0:
                    continue  # Terme non trouvé
                
                # IDF = log(N/DF)
                idf = math.log(total_docs / df)
                
                # Récupérer tous les documents contenant ce terme
                cursor.execute('''
                    SELECT tf.document_id, tf.tf_score, d.hash_id, d.content
                    FROM term_frequencies tf
                    JOIN documents d ON tf.document_id = d.id
                    WHERE tf.term = ?
                ''', (term,))
                
                for doc_id, tf_score, hash_id, content in cursor.fetchall():
                    tfidf_score = tf_score * idf
                    
                    if hash_id not in document_scores:
                        document_scores[hash_id] = {
                            'score': 0,
                            'content': content,
                            'hash_id': hash_id
                        }
                    
                    document_scores[hash_id]['score'] += tfidf_score
            
            conn.close()
            
            # Tri par score décroissant
            sorted_results = sorted(
                document_scores.values(), 
                key=lambda x: x['score'], 
                reverse=True
            )
            
            # Formatage des résultats
            results = []
            for i, result in enumerate(sorted_results[:limit]):
                # Extraction basique des métadonnées du contenu
                job_info = self.extract_job_info(result['content'])
                
                results.append({
                    'hash_id': result['hash_id'],
                    'content': result['content'][:300] + "...",
                    'tfidf_score': round(result['score'], 4),
                    'search_method': 'tfidf',
                    'rank': i + 1,
                    **job_info  # Ajouter les infos extraites
                })
            
            logger.info(f"🔍 TF-IDF: {len(results)} résultats pour '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"Erreur recherche TF-IDF: {e}")
            return []
    
    def build_job_content(self, job_data: Dict[str, Any]) -> str:
        """Construit le contenu textuel d'une offre"""
        parts = [
            job_data.get('title', ''),
            job_data.get('company', ''),
            job_data.get('location', ''),
            job_data.get('description', ''),
            ' '.join(job_data.get('technologies', [])),
            job_data.get('experience_level', ''),
            ' '.join(job_data.get('requirements', []))
        ]
        
        return ' '.join(filter(None, parts))
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenisation et nettoyage du texte"""
        if not text:
            return []
        
        # Conversion en minuscules
        text = text.lower()
        
        # Suppression de la ponctuation et caractères spéciaux
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Séparation en mots
        words = text.split()
        
        # Filtrage des mots courts et des mots vides
        stop_words = {
            'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'et', 'ou', 'à', 'avec',
            'pour', 'dans', 'sur', 'par', 'en', 'au', 'aux', 'ce', 'cette', 'ces',
            'il', 'elle', 'nous', 'vous', 'ils', 'elles', 'mon', 'ma', 'mes', 'ton',
            'ta', 'tes', 'son', 'sa', 'ses', 'notre', 'votre', 'leur', 'leurs',
            'que', 'qui', 'dont', 'quoi', 'où', 'quand', 'comment', 'pourquoi',
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might'
        }
        
        # Filtrer les mots courts et les mots vides
        filtered_words = [
            word for word in words 
            if len(word) > 2 and word not in stop_words
        ]
        
        return filtered_words
    
    def extract_job_info(self, content: str) -> Dict[str, Any]:
        """Extrait les informations basiques d'une offre depuis le contenu"""
        lines = content.split('\n')
        
        # Extraction basique - améliorer selon le format de vos données
        job_info = {
            'title': 'Titre non disponible',
            'company': 'Entreprise non disponible',
            'location': 'Localisation non disponible',
            'technologies': [],
            'experience_level': 'mid',
            'remote': False
        }
        
        # Patterns basiques pour l'extraction
        content_lower = content.lower()
        
        # Détection remote
        if any(word in content_lower for word in ['remote', 'télétravail', 'distanciel']):
            job_info['remote'] = True
        
        # Détection niveau d'expérience
        if any(word in content_lower for word in ['junior', 'débutant', 'stage']):
            job_info['experience_level'] = 'junior'
        elif any(word in content_lower for word in ['senior', 'lead', 'expert']):
            job_info['experience_level'] = 'senior'
        
        # Technologies courantes
        common_techs = [
            'python', 'javascript', 'java', 'react', 'vue', 'angular', 'node.js',
            'sql', 'postgresql', 'mongodb', 'docker', 'kubernetes', 'aws', 'azure'
        ]
        
        found_techs = [tech for tech in common_techs if tech in content_lower]
        job_info['technologies'] = found_techs
        
        return job_info
    
    def generate_hash(self, content: str) -> str:
        """Génère un hash pour le contenu"""
        import hashlib
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du moteur TF-IDF"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Nombre de documents indexés
            cursor.execute('SELECT COUNT(*) FROM documents')
            total_docs = cursor.fetchone()[0]
            
            # Nombre de termes uniques
            cursor.execute('SELECT COUNT(DISTINCT term) FROM term_frequencies')
            unique_terms = cursor.fetchone()[0]
            
            # Terme le plus fréquent
            cursor.execute('''
                SELECT term, SUM(frequency) as total_freq
                FROM term_frequencies 
                GROUP BY term 
                ORDER BY total_freq DESC 
                LIMIT 1
            ''')
            top_term = cursor.fetchone()
            
            conn.close()
            
            return {
                'indexed_documents': total_docs,
                'unique_terms': unique_terms,
                'top_term': {
                    'term': top_term[0] if top_term else None,
                    'frequency': top_term[1] if top_term else 0
                },
                'search_method': 'tfidf',
                'database_path': self.db_path
            }
            
        except Exception as e:
            logger.error(f"Erreur stats TF-IDF: {e}")
            return {'error': str(e)}
    
    def rebuild_index(self) -> bool:
        """Reconstruit l'index TF-IDF (utile pour maintenance)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Supprimer les anciens index
            cursor.execute('DELETE FROM term_frequencies')
            cursor.execute('DELETE FROM documents')
            
            conn.commit()
            conn.close()
            
            logger.info("🔄 Index TF-IDF reconstruit")
            return True
            
        except Exception as e:
            logger.error(f"Erreur reconstruction index: {e}")
            return False
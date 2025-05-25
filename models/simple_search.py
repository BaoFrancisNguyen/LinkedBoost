# models/simple_search.py - Moteur de recherche TF-IDF simple
import sqlite3
import json
import re
from typing import List, Dict, Any, Optional
from collections import Counter
import logging
import os

logger = logging.getLogger(__name__)

class SimpleSearchEngine:
    """Moteur de recherche simple basé sur TF-IDF et correspondance de mots-clés"""
    
    def __init__(self):
        self.db_path = "data/simple_search.db"
        self.stop_words = self.load_stop_words()
        self.tech_keywords = self.load_tech_keywords()
        self.initialize_db()
    
    def initialize_db(self):
        """Initialise la base de données SQLite"""
        os.makedirs("data", exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table principale pour les documents
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_hash TEXT UNIQUE,
                title TEXT,
                company TEXT,
                location TEXT,
                description TEXT,
                technologies TEXT,
                experience_level TEXT,
                remote BOOLEAN,
                salary_text TEXT,
                url TEXT,
                source TEXT,
                full_content TEXT,
                keywords TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table pour les statistiques de recherche
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                results_count INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Base de données de recherche simple initialisée")
    
    def load_stop_words(self) -> set:
        """Charge les mots vides français et anglais"""
        french_stop_words = {
            'le', 'de', 'et', 'à', 'un', 'il', 'être', 'et', 'en', 'avoir', 'que', 'pour',
            'dans', 'ce', 'son', 'une', 'sur', 'avec', 'ne', 'se', 'pas', 'tout', 'plus',
            'par', 'grand', 'en', 'même', 'aussi', 'leur', 'bien', 'où', 'ou', 'alors',
            'nous', 'vous', 'ils', 'elle', 'très', 'encore', 'sans', 'entre', 'contre'
        }
        
        english_stop_words = {
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for',
            'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this', 'but', 'his',
            'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my',
            'one', 'all', 'would', 'there', 'their', 'what', 'so', 'up', 'out', 'if'
        }
        
        return french_stop_words.union(english_stop_words)
    
    def load_tech_keywords(self) -> Dict[str, List[str]]:
        """Charge les mots-clés techniques par catégorie"""
        return {
            'languages': [
                'python', 'javascript', 'java', 'typescript', 'go', 'rust', 'php', 'ruby',
                'c++', 'c#', 'scala', 'kotlin', 'swift', 'dart', 'r', 'matlab'
            ],
            'frameworks': [
                'react', 'vue', 'angular', 'django', 'flask', 'spring', 'laravel',
                'node.js', 'express', 'fastapi', 'next.js', 'nuxt.js', 'svelte'
            ],
            'databases': [
                'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'sqlite',
                'oracle', 'cassandra', 'neo4j', 'dynamodb', 'firebase'
            ],
            'cloud': [
                'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'heroku', 'vercel',
                'netlify', 'digitalocean', 'linode'
            ],
            'tools': [
                'git', 'jenkins', 'gitlab', 'github', 'terraform', 'ansible',
                'chef', 'puppet', 'vagrant', 'nginx', 'apache'
            ],
            'data': [
                'pandas', 'numpy', 'tensorflow', 'pytorch', 'scikit-learn', 'spark',
                'hadoop', 'kafka', 'airflow', 'tableau', 'powerbi'
            ]
        }
    
    def clean_text(self, text: str) -> str:
        """Nettoie et normalise le texte"""
        if not text:
            return ""
        
        # Conversion en minuscules
        text = text.lower()
        
        # Suppression des caractères spéciaux (garde les lettres, chiffres, espaces)
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Suppression des espaces multiples
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extrait les mots-clés importants du texte"""
        cleaned_text = self.clean_text(text)
        words = cleaned_text.split()
        
        # Filtrage des mots vides et mots trop courts
        keywords = [
            word for word in words 
            if len(word) > 2 and word not in self.stop_words
        ]
        
        # Ajout des technologies détectées avec poids plus élevé
        tech_found = []
        for category, techs in self.tech_keywords.items():
            for tech in techs:
                if tech in cleaned_text:
                    tech_found.extend([tech] * 2)  # Poids double pour les technologies
        
        keywords.extend(tech_found)
        
        return keywords
    
    def calculate_term_frequency(self, keywords: List[str]) -> Dict[str, float]:
        """Calcule la fréquence des termes"""
        if not keywords:
            return {}
        
        keyword_count = Counter(keywords)
        total_keywords = len(keywords)
        
        tf = {}
        for keyword, count in keyword_count.items():
            tf[keyword] = count / total_keywords
        
        return tf
    
    def store_job(self, job_data: Dict[str, Any]) -> bool:
        """Stocke une offre d'emploi dans la base"""
        try:
            # Construction du texte complet
            full_content = self.build_full_content(job_data)
            content_hash = self.generate_hash(full_content)
            
            # Extraction des mots-clés
            keywords = self.extract_keywords(full_content)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Vérification unicité
            cursor.execute('SELECT 1 FROM job_documents WHERE content_hash = ?', (content_hash,))
            if cursor.fetchone():
                conn.close()
                return False  # Déjà existant
            
            # Insertion
            cursor.execute('''
                INSERT INTO job_documents (
                    content_hash, title, company, location, description,
                    technologies, experience_level, remote, salary_text,
                    url, source, full_content, keywords
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                content_hash,
                job_data.get('title', ''),
                job_data.get('company', ''),
                job_data.get('location', ''),
                job_data.get('description', ''),
                json.dumps(job_data.get('technologies', [])),
                job_data.get('experience_level', ''),
                job_data.get('remote', False),
                job_data.get('salary', {}).get('text', ''),
                job_data.get('url', ''),
                job_data.get('source', ''),
                full_content,
                json.dumps(keywords)
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"✅ Offre stockée: {job_data.get('title', 'Sans titre')}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur stockage offre: {e}")
            return False
    
    def search_jobs(self, query: str, limit: int = 20, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Recherche des offres d'emploi"""
        if not query.strip():
            return []
        
        try:
            # Nettoyage et extraction des mots-clés de la requête
            query_keywords = self.extract_keywords(query)
            if not query_keywords:
                return []
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Construction de la requête SQL avec scoring
            search_conditions = []
            params = []
            
            # Recherche par mots-clés dans le contenu complet
            keyword_conditions = []
            for keyword in query_keywords[:10]:  # Limite à 10 mots-clés pour la performance
                keyword_conditions.append("full_content LIKE ?")
                params.append(f"%{keyword}%")
            
            if keyword_conditions:
                search_conditions.append(f"({' OR '.join(keyword_conditions)})")
            
            # Filtres additionnels
            if filters:
                if filters.get('company'):
                    search_conditions.append("company LIKE ?")
                    params.append(f"%{filters['company']}%")
                
                if filters.get('location'):
                    search_conditions.append("location LIKE ?")
                    params.append(f"%{filters['location']}%")
                
                if filters.get('experience_level'):
                    search_conditions.append("experience_level = ?")
                    params.append(filters['experience_level'])
                
                if filters.get('remote') is not None:
                    search_conditions.append("remote = ?")
                    params.append(filters['remote'])
            
            # Requête finale avec scoring basique
            where_clause = " AND ".join(search_conditions) if search_conditions else "1=1"
            
            sql_query = f'''
                SELECT content_hash, title, company, location, description,
                       technologies, experience_level, remote, url, source,
                       salary_text, keywords, full_content
                FROM job_documents
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
            '''
            params.append(limit * 2)  # Récupérer plus pour le scoring
            
            cursor.execute(sql_query, params)
            rows = cursor.fetchall()
            
            # Calcul du score de pertinence
            scored_results = []
            for row in rows:
                score = self.calculate_relevance_score(query_keywords, row)
                if score > 0:
                    job_data = self.format_job_result(row, score)
                    scored_results.append(job_data)
            
            # Tri par score décroissant
            scored_results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # Enregistrement des stats de recherche
            self.log_search_stats(query, len(scored_results))
            
            conn.close()
            
            logger.info(f"🔍 Recherche '{query}': {len(scored_results)} résultats")
            return scored_results[:limit]
            
        except Exception as e:
            logger.error(f"Erreur recherche: {e}")
            return []
    
    def calculate_relevance_score(self, query_keywords: List[str], job_row: tuple) -> float:
        """Calcule un score de pertinence pour une offre"""
        try:
            full_content = job_row[12]  # Index du full_content
            title = job_row[1]
            stored_keywords = json.loads(job_row[11]) if job_row[11] else []
            
            score = 0.0
            
            # Score basé sur la présence des mots-clés
            content_lower = full_content.lower()
            title_lower = title.lower()
            
            for keyword in query_keywords:
                keyword_lower = keyword.lower()
                
                # Bonus si le mot-clé est dans le titre (poids x3)
                if keyword_lower in title_lower:
                    score += 3.0
                
                # Bonus si le mot-clé est dans le contenu complet
                if keyword_lower in content_lower:
                    score += 1.0
                
                # Bonus si c'est un mot-clé stocké (technologies, etc.)
                if keyword_lower in [k.lower() for k in stored_keywords]:
                    score += 2.0
            
            # Normalisation du score
            if query_keywords:
                score = score / len(query_keywords)
            
            return min(score, 10.0)  # Score maximum de 10
            
        except Exception as e:
            logger.debug(f"Erreur calcul score: {e}")
            return 0.0
    
    def format_job_result(self, row: tuple, score: float) -> Dict[str, Any]:
        """Formate un résultat de recherche"""
        try:
            technologies = json.loads(row[5]) if row[5] else []
        except:
            technologies = []
        
        return {
            'content_hash': row[0],
            'title': row[1],
            'company': row[2],
            'location': row[3],
            'description': row[4][:300] + "..." if len(row[4]) > 300 else row[4],
            'technologies': technologies,
            'experience_level': row[6],
            'remote': bool(row[7]),
            'url': row[8],
            'source': row[9],
            'salary_text': row[10],
            'relevance_score': round(score, 2),
            'search_method': 'tfidf_simple'
        }
    
    def build_full_content(self, job_data: Dict[str, Any]) -> str:
        """Construit le contenu complet pour l'indexation"""
        parts = [
            job_data.get('title', ''),
            job_data.get('company', ''),
            job_data.get('location', ''),
            job_data.get('description', ''),
            ' '.join(job_data.get('technologies', [])),
            job_data.get('experience_level', ''),
            ' '.join(job_data.get('requirements', [])),
        ]
        
        return ' '.join(filter(None, parts))
    
    def generate_hash(self, content: str) -> str:
        """Génère un hash pour le contenu"""
        import hashlib
        return hashlib.md5(content.encode()).hexdigest()
    
    def log_search_stats(self, query: str, results_count: int):
        """Enregistre les statistiques de recherche"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO search_stats (query, results_count)
                VALUES (?, ?)
            ''', (query[:100], results_count))  # Limite la longueur de la requête
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.debug(f"Erreur log stats: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du moteur de recherche"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Nombre total de documents
            cursor.execute('SELECT COUNT(*) FROM job_documents')
            total_docs = cursor.fetchone()[0]
            
            # Nombre de recherches effectuées
            cursor.execute('SELECT COUNT(*) FROM search_stats')
            total_searches = cursor.fetchone()[0]
            
            # Recherches récentes
            cursor.execute('''
                SELECT query, results_count, timestamp 
                FROM search_stats 
                ORDER BY timestamp DESC 
                LIMIT 5
            ''')
            recent_searches = cursor.fetchall()
            
            # Technologies les plus présentes
            cursor.execute('SELECT technologies FROM job_documents WHERE technologies IS NOT NULL')
            tech_data = cursor.fetchall()
            
            tech_counter = Counter()
            for row in tech_data:
                try:
                    technologies = json.loads(row[0])
                    tech_counter.update(technologies)
                except:
                    continue
            
            top_technologies = tech_counter.most_common(10)
            
            conn.close()
            
            return {
                'total_documents': total_docs,
                'total_searches': total_searches,
                'recent_searches': [
                    {'query': r[0], 'results': r[1], 'timestamp': r[2]}
                    for r in recent_searches
                ],
                'top_technologies': [
                    {'name': tech, 'count': count}
                    for tech, count in top_technologies
                ],
                'search_method': 'tfidf_simple',
                'database_path': self.db_path
            }
            
        except Exception as e:
            logger.error(f"Erreur récupération stats: {e}")
            return {
                'total_documents': 0,
                'error': str(e),
                'search_method': 'tfidf_simple'
            }
    
    def get_search_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """Retourne des suggestions de recherche basées sur l'historique"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT DISTINCT query 
                FROM search_stats 
                WHERE query LIKE ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (f"%{partial_query}%", limit))
            
            suggestions = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            return suggestions
            
        except Exception as e:
            logger.debug(f"Erreur suggestions: {e}")
            return []
    
    def cleanup_old_searches(self, days_old: int = 30) -> int:
        """Nettoie les anciennes recherches"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM search_stats 
                WHERE timestamp < datetime('now', '-{} days')
            '''.format(days_old))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"🧹 {deleted_count} anciennes recherches supprimées")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Erreur nettoyage recherches: {e}")
            return 0
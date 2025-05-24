# RAG avec Ollama pour les embeddings
# models/embeddings_ollama.py

import requests
import json
import numpy as np
from typing import List, Dict, Any
import sqlite3
import logging
from config import Config

logger = logging.getLogger(__name__)

class OllamaEmbeddingManager:
    """Gestionnaire d'embeddings utilisant Ollama (sans Hugging Face)"""
    
    def __init__(self):
        self.base_url = Config.OLLAMA_BASE_URL
        self.embedding_model = "nomic-embed-text"  # Modèle d'embedding d'Ollama
        self.db_path = "data/embeddings.db"
        self.initialize_db()
        
        # Vérifier si le modèle d'embedding est disponible
        self.ensure_embedding_model()
    
    def ensure_embedding_model(self):
        """S'assure que le modèle d'embedding est disponible"""
        try:
            # Tenter de télécharger le modèle d'embedding si pas présent
            import subprocess
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            
            if "nomic-embed-text" not in result.stdout:
                logger.info("📥 Téléchargement du modèle d'embedding...")
                subprocess.run(['ollama', 'pull', 'nomic-embed-text'], check=True)
                logger.info("✅ Modèle d'embedding installé")
            else:
                logger.info("✅ Modèle d'embedding disponible")
                
        except Exception as e:
            logger.warning(f"⚠️ Impossible d'installer le modèle d'embedding: {e}")
            logger.info("💡 Utilisez: ollama pull nomic-embed-text")
    
    def initialize_db(self):
        """Initialise la base de données SQLite pour les embeddings"""
        import os
        os.makedirs("data", exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table pour stocker les embeddings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_hash TEXT UNIQUE,
                content TEXT,
                embedding BLOB,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table pour les offres d'emploi
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                company TEXT,
                location TEXT,
                description TEXT,
                technologies TEXT,
                experience_level TEXT,
                remote BOOLEAN,
                salary_min INTEGER,
                salary_max INTEGER,
                url TEXT,
                source TEXT,
                content_hash TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (content_hash) REFERENCES embeddings (content_hash)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Base de données d'embeddings initialisée")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Génère un embedding avec Ollama"""
        try:
            # Nettoyage du texte
            clean_text = self.clean_text(text)
            
            # Requête à Ollama pour l'embedding
            payload = {
                "model": self.embedding_model,
                "prompt": clean_text
            }
            
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('embedding', [])
            else:
                logger.error(f"Erreur embedding Ollama: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Erreur génération embedding: {e}")
            return []
    
    def clean_text(self, text: str) -> str:
        """Nettoie le texte pour l'embedding"""
        import re
        
        if not text:
            return ""
        
        # Suppression des caractères spéciaux et normalisation
        text = re.sub(r'[^\w\s\-\.,;:!?]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Limite de longueur
        return text[:2000]
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calcule la similarité cosinus entre deux embeddings"""
        try:
            # Conversion en numpy arrays
            a = np.array(embedding1)
            b = np.array(embedding2)
            
            # Similarité cosinus
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            similarity = dot_product / (norm_a * norm_b)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Erreur calcul similarité: {e}")
            return 0.0
    
    async def store_job_with_embedding(self, job_data: Dict[str, Any]) -> bool:
        """Stocke une offre d'emploi avec son embedding"""
        try:
            # Construction du texte complet pour l'embedding
            full_text = self.build_job_text(job_data)
            content_hash = self.generate_hash(full_text)
            
            # Vérifier si déjà stocké
            if self.is_already_stored(content_hash):
                return False
            
            # Génération de l'embedding
            embedding = await self.generate_embedding(full_text)
            
            if not embedding:
                logger.warning("Embedding vide, impossible de stocker")
                return False
            
            # Stockage en base
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                # Stockage de l'embedding
                embedding_blob = json.dumps(embedding).encode('utf-8')
                metadata = json.dumps({
                    'job_id': job_data.get('hash_id', ''),
                    'source': job_data.get('source', ''),
                    'type': 'job_offer'
                })
                
                cursor.execute('''
                    INSERT INTO embeddings (content_hash, content, embedding, metadata)
                    VALUES (?, ?, ?, ?)
                ''', (content_hash, full_text, embedding_blob, metadata))
                
                # Stockage des données structurées
                cursor.execute('''
                    INSERT INTO job_offers (
                        title, company, location, description, technologies,
                        experience_level, remote, salary_min, salary_max,
                        url, source, content_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    job_data.get('title', ''),
                    job_data.get('company', ''),
                    job_data.get('location', ''),
                    job_data.get('description', ''),
                    json.dumps(job_data.get('technologies', [])),
                    job_data.get('experience_level', ''),
                    job_data.get('remote', False),
                    job_data.get('salary', {}).get('min'),
                    job_data.get('salary', {}).get('max'),
                    job_data.get('url', ''),
                    job_data.get('source', ''),
                    content_hash
                ))
                
                conn.commit()
                logger.debug(f"✅ Offre stockée: {job_data.get('title', 'Sans titre')}")
                return True
                
            except sqlite3.IntegrityError:
                logger.debug("Offre déjà existante, ignorée")
                return False
                
        except Exception as e:
            logger.error(f"Erreur stockage offre: {e}")
            return False
        finally:
            conn.close()
    
    async def search_similar_jobs(self, query: str, limit: int = 10, 
                                threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Recherche des offres similaires par similarité sémantique"""
        try:
            # Génération embedding de la requête
            query_embedding = await self.generate_embedding(query)
            
            if not query_embedding:
                return []
            
            # Récupération de tous les embeddings stockés
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT e.content_hash, e.content, e.embedding, e.metadata,
                       j.title, j.company, j.location, j.description,
                       j.technologies, j.experience_level, j.remote, j.url, j.source
                FROM embeddings e
                JOIN job_offers j ON e.content_hash = j.content_hash
                ORDER BY j.scraped_at DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            # Calcul de similarité pour chaque résultat
            similar_jobs = []
            
            for row in results:
                try:
                    stored_embedding = json.loads(row[2].decode('utf-8'))
                    similarity = self.calculate_similarity(query_embedding, stored_embedding)
                    
                    if similarity >= threshold:
                        job_data = {
                            'content_hash': row[0],
                            'content': row[1],
                            'similarity_score': similarity,
                            'title': row[4],
                            'company': row[5],
                            'location': row[6],
                            'description': row[7][:300] + "..." if len(row[7]) > 300 else row[7],
                            'technologies': json.loads(row[8]) if row[8] else [],
                            'experience_level': row[9],
                            'remote': bool(row[10]),
                            'url': row[11],
                            'source': row[12]
                        }
                        similar_jobs.append(job_data)
                        
                except Exception as e:
                    logger.debug(f"Erreur traitement résultat: {e}")
                    continue
            
            # Tri par similarité décroissante
            similar_jobs.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            logger.info(f"🔍 Trouvé {len(similar_jobs)} offres similaires pour '{query[:50]}...'")
            return similar_jobs[:limit]
            
        except Exception as e:
            logger.error(f"Erreur recherche similarité: {e}")
            return []
    
    def build_job_text(self, job_data: Dict[str, Any]) -> str:
        """Construit le texte complet d'une offre pour l'embedding"""
        parts = [
            job_data.get('title', ''),
            job_data.get('company', ''),
            job_data.get('location', ''),
            job_data.get('description', ''),
            ' '.join(job_data.get('technologies', [])),
            job_data.get('experience_level', '')
        ]
        
        return ' '.join(filter(None, parts))
    
    def generate_hash(self, text: str) -> str:
        """Génère un hash pour le contenu"""
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()
    
    def is_already_stored(self, content_hash: str) -> bool:
        """Vérifie si le contenu est déjà stocké"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT 1 FROM embeddings WHERE content_hash = ?', (content_hash,))
        exists = cursor.fetchone() is not None
        
        conn.close()
        return exists
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de la base d'embeddings"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Comptage total
            cursor.execute('SELECT COUNT(*) FROM job_offers')
            total_jobs = cursor.fetchone()[0]
            
            # Comptage par source
            cursor.execute('SELECT source, COUNT(*) FROM job_offers GROUP BY source')
            sources = dict(cursor.fetchall())
            
            # Dernière mise à jour
            cursor.execute('SELECT MAX(scraped_at) FROM job_offers')
            last_update = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_jobs': total_jobs,
                'sources': sources,
                'last_update': last_update,
                'embedding_model': self.embedding_model,
                'database_path': self.db_path
            }
            
        except Exception as e:
            logger.error(f"Erreur récupération stats: {e}")
            return {'error': str(e)}


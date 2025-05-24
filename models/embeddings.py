# models/embeddings.py - Gestion des embeddings
import numpy as np
import logging
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from config import Config

logger = logging.getLogger(__name__)

class EmbeddingManager:
    """Gestionnaire des embeddings pour la recherche sémantique"""
    
    def __init__(self):
        self.model = None
        self.chroma_client = None
        self.collection = None
        self.initialize()
    
    def initialize(self):
        """Initialise le modèle d'embeddings et ChromaDB"""
        try:
            # Chargement du modèle d'embeddings
            logger.info(f"🔄 Chargement du modèle d'embeddings {Config.EMBEDDING_MODEL}...")
            self.model = SentenceTransformer(Config.EMBEDDING_MODEL)
            logger.info("✅ ChromaDB initialisé")
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation embeddings: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Génère un embedding pour un texte donné"""
        try:
            if not self.model:
                raise Exception("Modèle d'embeddings non initialisé")
            
            # Nettoyage du texte
            clean_text = self.clean_text_for_embedding(text)
            
            # Génération de l'embedding
            embedding = self.model.encode(clean_text, convert_to_tensor=False)
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Erreur génération embedding: {e}")
            return []
    
    def clean_text_for_embedding(self, text: str) -> str:
        """Nettoie le texte pour l'embedding"""
        import re
        
        if not text:
            return ""
        
        # Suppression des caractères spéciaux et normalisation
        text = re.sub(r'[^\w\s\-\.,;:!?]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Limite de longueur pour les embeddings
        return text[:2000]
    
    async def search_similar_jobs(self, query: str, limit: int = 10, 
                                threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Recherche des offres similaires par similarité sémantique"""
        try:
            # Génération embedding de la requête
            query_embedding = await self.generate_embedding(query)
            
            if not query_embedding:
                return []
            
            # Recherche dans ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Formatage des résultats
            similar_jobs = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    distance = results['distances'][0][i]
                    similarity = 1 - distance  # Conversion distance -> similarité
                    
                    if similarity >= threshold:
                        job_data = results['metadatas'][0][i]
                        job_data['similarity_score'] = similarity
                        job_data['content'] = doc
                        similar_jobs.append(job_data)
            
            logger.info(f"🔍 Trouvé {len(similar_jobs)} offres similaires pour '{query[:50]}...'")
            return similar_jobs
            
        except Exception as e:
            logger.error(f"Erreur recherche similarité: {e}")
            return []
    
    async def add_job_to_index(self, job: Dict[str, Any]) -> bool:
        """Ajoute une offre à l'index vectoriel"""
        try:
            # Construction du texte complet pour l'embedding
            full_text = self.build_job_text(job)
            
            # Génération de l'embedding
            embedding = await self.generate_embedding(full_text)
            
            if not embedding:
                return False
            
            # Ajout à ChromaDB
            self.collection.add(
                documents=[full_text],
                embeddings=[embedding],
                metadatas=[{
                    'job_id': job.get('hash_id', ''),
                    'title': job.get('title', ''),
                    'company': job.get('company', ''),
                    'location': job.get('location', ''),
                    'source': job.get('source', ''),
                    'experience_level': job.get('experience_level', ''),
                    'remote': job.get('remote', False),
                    'technologies': ','.join(job.get('technologies', [])),
                    'scraped_at': job.get('scraped_at', ''),
                    'url': job.get('url', '')
                }],
                ids=[job.get('hash_id', f"job_{hash(full_text)}")]
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur ajout job à l'index: {e}")
            return False
    
    def build_job_text(self, job: Dict[str, Any]) -> str:
        """Construit le texte complet d'une offre pour l'embedding"""
        parts = [
            job.get('title', ''),
            job.get('company', ''),
            job.get('location', ''),
            job.get('description', ''),
            ' '.join(job.get('requirements', [])),
            ' '.join(job.get('technologies', []))
        ]
        
        return ' '.join(filter(None, parts))
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de la collection"""
        try:
            count = self.collection.count()
            return {
                'total_jobs': count,
                'model': Config.EMBEDDING_MODEL,
                'collection_name': self.collection.name
            }
        except Exception as e:
            logger.error(f"Erreur récupération stats: {e}")
            return {'total_jobs': 0, 'error': str(e)}
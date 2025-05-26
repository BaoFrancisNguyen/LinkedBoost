# models/embeddings.py - Version sans Hugging Face (fix import)

import numpy as np
import logging
from typing import List, Dict, Any, Optional
import sqlite3
import json
from config import Config

logger = logging.getLogger(__name__)

class EmbeddingManager:
    """Gestionnaire d'embeddings SANS Hugging Face - Version corrigée"""
    
    def __init__(self):
        self.model = None
        self.method = "ollama"  # ou "simple" en fallback
        self.initialize()
    
    def initialize(self):
        """Initialise le gestionnaire d'embeddings"""
        try:
            # Essayer d'abord Ollama
            self.initialize_ollama()
            self.method = "ollama"
            logger.info("✅ Embeddings Ollama initialisés")
            
        except Exception as e:
            logger.warning(f"⚠️ Ollama embeddings non disponible: {e}")
            
            try:
                # Fallback vers une méthode simple
                self.initialize_simple()
                self.method = "simple"
                logger.info("✅ Embeddings simples initialisés")
                
            except Exception as e2:
                logger.error(f"❌ Erreur initialisation embeddings: {e2}")
                self.method = "none"
    
    def initialize_ollama(self):
        """Initialise les embeddings avec Ollama"""
        import requests
        
        # Tester la connexion Ollama
        response = requests.get(f"{Config.OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code != 200:
            raise Exception("Ollama non disponible")
        
        self.model = "nomic-embed-text"  # Modèle d'embedding d'Ollama
        logger.info("🤖 Embeddings Ollama configurés")
    
    def initialize_simple(self):
        """Initialise un système d'embeddings simple basé sur TF-IDF"""
        from collections import Counter
        import re
        
        # Utiliser TF-IDF simple comme fallback
        self.model = "tfidf"
        logger.info("📊 Embeddings TF-IDF configurés")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Génère un embedding selon la méthode disponible"""
        try:
            if self.method == "ollama":
                return await self.generate_ollama_embedding(text)
            elif self.method == "simple":
                return self.generate_simple_embedding(text)
            else:
                return []
                
        except Exception as e:
            logger.error(f"Erreur génération embedding: {e}")
            return []
    
    async def generate_ollama_embedding(self, text: str) -> List[float]:
        """Génère un embedding avec Ollama"""
        import requests
        
        try:
            clean_text = self.clean_text(text)
            
            payload = {
                "model": self.model,
                "prompt": clean_text
            }
            
            response = requests.post(
                f"{Config.OLLAMA_BASE_URL}/api/embeddings",
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
            logger.error(f"Erreur embedding Ollama: {e}")
            return []
    
    def generate_simple_embedding(self, text: str) -> List[float]:
        """Génère un embedding simple basé sur TF-IDF"""
        try:
            import re
            from collections import Counter
            import math
            
            # Nettoyage du texte
            clean_text = self.clean_text(text).lower()
            
            # Tokenisation simple
            words = re.findall(r'\b\w+\b', clean_text)
            
            # Vocabulaire de base (mots-clés techniques)
            base_vocab = [
                'python', 'javascript', 'java', 'react', 'vue', 'angular', 'node',
                'sql', 'mongodb', 'postgresql', 'aws', 'azure', 'docker', 'git',
                'machine learning', 'ai', 'data', 'senior', 'junior', 'développeur',
                'chef', 'projet', 'manager', 'lead', 'architect', 'full stack',
                'frontend', 'backend', 'devops', 'agile', 'scrum', 'remote',
                'télétravail', 'paris', 'lyon', 'marseille', 'cdi', 'stage'
            ]
            
            # Calculer TF-IDF simplifié
            word_count = Counter(words)
            total_words = len(words)
            
            embedding = []
            for vocab_word in base_vocab:
                # Term Frequency
                tf = word_count.get(vocab_word, 0) / total_words if total_words > 0 else 0
                
                # IDF simplifié (on assume une collection de documents)
                idf = math.log(1000 / (1 + sum(1 for w in words if vocab_word in w)))
                
                # TF-IDF
                tfidf = tf * idf
                embedding.append(tfidf)
            
            # Normalisation
            norm = math.sqrt(sum(x*x for x in embedding))
            if norm > 0:
                embedding = [x/norm for x in embedding]
            
            return embedding
            
        except Exception as e:
            logger.error(f"Erreur embedding simple: {e}")
            return [0.0] * 50  # Embedding par défaut
    
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
    
    async def search_similar_jobs(self, query: str, limit: int = 10, 
                                threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Recherche des offres similaires (placeholder)"""
        try:
            # Pour l'instant, retourner une liste vide
            # Ceci sera implémenté quand la base de données sera prête
            logger.info(f"🔍 Recherche similarité pour: {query[:50]}...")
            return []
            
        except Exception as e:
            logger.error(f"Erreur recherche similarité: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du système d'embeddings"""
        return {
            'method': self.method,
            'model': self.model,
            'available': self.method != "none",
            'embedding_size': 50 if self.method == "simple" else 384
        }
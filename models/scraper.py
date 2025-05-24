# models/scraper.py - Scraping orchestrator
import asyncio
import time
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from scrapers.wttj_scraper import WTTJScraper
from scrapers.linkedin_scraper import LinkedInScraper
from models.embeddings import EmbeddingManager
from models.knowledge_base import KnowledgeBase
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScrapingOrchestrator:
    """Orchestrateur principal pour le scraping multi-sites"""
    
    def __init__(self):
        self.scrapers = {
            'wttj': WTTJScraper(),
            'linkedin': LinkedInScraper()
        }
        self.embedding_manager = EmbeddingManager()
        self.knowledge_base = KnowledgeBase()
        self.last_scrape = None
        self.scraping_stats = {
            'total_jobs': 0,
            'last_update': None,
            'errors': []
        }
    
    async def run_full_scrape(self, sources: List[str] = None) -> Dict[str, Any]:
        """Lance un scraping complet de toutes les sources"""
        if sources is None:
            sources = ['wttj']  # Commencer par WTTJ, moins risqué
        
        logger.info(f"🚀 Début du scraping pour : {sources}")
        start_time = datetime.now()
        all_jobs = []
        
        for source in sources:
            if source not in self.scrapers:
                logger.warning(f"❌ Scraper {source} non disponible")
                continue
                
            try:
                logger.info(f"📡 Scraping {source}...")
                scraper = self.scrapers[source]
                jobs = await scraper.scrape_jobs(limit=Config.MAX_JOBS_PER_SCRAPE)
                
                logger.info(f"✅ {len(jobs)} offres récupérées de {source}")
                all_jobs.extend(jobs)
                
                # Délai entre sources
                await asyncio.sleep(Config.REQUEST_DELAY)
                
            except Exception as e:
                error_msg = f"Erreur scraping {source}: {str(e)}"
                logger.error(error_msg)
                self.scraping_stats['errors'].append({
                    'source': source,
                    'error': error_msg,
                    'timestamp': datetime.now().isoformat()
                })
        
        # Traitement et stockage
        if all_jobs:
            processed_jobs = await self.process_jobs(all_jobs)
            await self.store_jobs(processed_jobs)
        
        # Mise à jour des stats
        self.scraping_stats.update({
            'total_jobs': len(all_jobs),
            'last_update': datetime.now().isoformat(),
            'duration_seconds': (datetime.now() - start_time).total_seconds()
        })
        
        logger.info(f"🎉 Scraping terminé : {len(all_jobs)} offres en {self.scraping_stats['duration_seconds']:.1f}s")
        return self.scraping_stats
    
    async def process_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Traite et nettoie les offres d'emploi"""
        logger.info(f"🔄 Traitement de {len(jobs)} offres...")
        
        processed = []
        for job in jobs:
            try:
                # Nettoyage et normalisation
                clean_job = {
                    'title': self.clean_text(job.get('title', '')),
                    'company': self.clean_text(job.get('company', '')),
                    'location': self.clean_text(job.get('location', '')),
                    'description': self.clean_text(job.get('description', '')),
                    'requirements': self.extract_requirements(job.get('description', '')),
                    'salary': self.extract_salary(job.get('description', '')),
                    'remote': self.detect_remote(job.get('description', '') + ' ' + job.get('title', '')),
                    'experience_level': self.detect_experience_level(job.get('title', '') + ' ' + job.get('description', '')),
                    'technologies': self.extract_technologies(job.get('description', '')),
                    'url': job.get('url', ''),
                    'source': job.get('source', 'unknown'),
                    'scraped_at': datetime.now().isoformat(),
                    'hash_id': self.generate_job_hash(job)
                }
                
                # Génération d'embedding pour le contenu complet
                full_text = f"{clean_job['title']} {clean_job['company']} {clean_job['description']}"
                clean_job['embedding'] = await self.embedding_manager.generate_embedding(full_text)
                
                processed.append(clean_job)
                
            except Exception as e:
                logger.error(f"Erreur traitement offre: {e}")
                continue
        
        logger.info(f"✅ {len(processed)} offres traitées avec succès")
        return processed
    
    def clean_text(self, text: str) -> str:
        """Nettoie le texte des offres"""
        import re
        if not text:
            return ""
        
        # Suppression HTML et caractères spéciaux
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text[:5000]  # Limite de longueur
    
    def extract_requirements(self, description: str) -> List[str]:
        """Extrait les compétences requises"""
        import re
        
        requirements = []
        patterns = [
            r'(?:compétences?|skills?|requis|required)[:\-\s]+(.*?)(?:\n|\.|;)',
            r'(?:maîtrise|experience)[:\-\s]+(.*?)(?:\n|\.|;)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                # Découpage par virgules/points
                skills = re.split(r'[,;]+', match)
                requirements.extend([skill.strip() for skill in skills if skill.strip()])
        
        return list(set(requirements))[:10]  # Max 10 compétences
    
    def extract_salary(self, description: str) -> Dict[str, Any]:
        """Extrait les informations de salaire"""
        import re
        
        salary_patterns = [
            r'(\d+)k?\s*[-–]\s*(\d+)k?\s*€',
            r'(\d+)\s*k€',
            r'(\d+)\s*euros?',
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return {
                    'found': True,
                    'text': match.group(0),
                    'min': int(match.group(1)) * 1000 if 'k' in match.group(0) else int(match.group(1)),
                    'max': int(match.group(2)) * 1000 if len(match.groups()) > 1 and 'k' in match.group(0) else None
                }
        
        return {'found': False, 'text': '', 'min': None, 'max': None}
    
    def detect_remote(self, text: str) -> bool:
        """Détecte si le poste est en remote"""
        remote_keywords = ['remote', 'télétravail', 'home office', 'distanciel', 'hybride']
        return any(keyword in text.lower() for keyword in remote_keywords)
    
    def detect_experience_level(self, text: str) -> str:
        """Détecte le niveau d'expérience requis"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['senior', 'lead', 'principal', '5+ ans', '7+ ans']):
            return 'senior'
        elif any(word in text_lower for word in ['junior', 'débutant', '0-2 ans', 'stage']):
            return 'junior'
        else:
            return 'mid'
    
    def extract_technologies(self, description: str) -> List[str]:
        """Extrait les technologies mentionnées"""
        tech_keywords = [
            'python', 'javascript', 'react', 'vue', 'angular', 'node.js', 'java',
            'sql', 'postgresql', 'mongodb', 'redis', 'docker', 'kubernetes',
            'aws', 'azure', 'gcp', 'tensorflow', 'pytorch', 'git', 'jenkins',
            'html', 'css', 'typescript', 'go', 'rust', 'c++', 'php', 'ruby'
        ]
        
        found_techs = []
        description_lower = description.lower()
        
        for tech in tech_keywords:
            if tech in description_lower:
                found_techs.append(tech)
        
        return found_techs
    
    def generate_job_hash(self, job: Dict) -> str:
        """Génère un hash unique pour l'offre"""
        import hashlib
        
        unique_string = f"{job.get('title', '')}{job.get('company', '')}{job.get('url', '')}"
        return hashlib.md5(unique_string.encode()).hexdigest()
    
    async def store_jobs(self, jobs: List[Dict]) -> None:
        """Stocke les offres dans la base de connaissances"""
        logger.info(f"💾 Stockage de {len(jobs)} offres...")
        
        for job in jobs:
            try:
                await self.knowledge_base.store_job(job)
            except Exception as e:
                logger.error(f"Erreur stockage offre {job.get('title', 'Unknown')}: {e}")
        
        logger.info("✅ Stockage terminé")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de scraping"""
        return {
            **self.scraping_stats,
            'available_scrapers': list(self.scrapers.keys()),
            'knowledge_base_stats': self.knowledge_base.get_stats()
        }
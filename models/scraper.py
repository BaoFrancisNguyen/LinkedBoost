# models/scraper.py - Intégration du scraper LinkedIn

import asyncio
import time
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
import json
import os

# Import des scrapers - MISE À JOUR
from scrapers.wttj_scraper import WTTJScraper
from scrapers.linkedin_scraper import LinkedInScraper  # ✅ NOUVEAU
from models.embeddings import EmbeddingManager
from models.knowledge_base import KnowledgeBase
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScrapingOrchestrator:
    """Orchestrateur principal pour le scraping - Avec LinkedIn intégré"""
    
    def __init__(self):
        # ✅ SCRAPERS DISPONIBLES - LinkedIn ajouté
        self.scrapers = {
            'wttj': WTTJScraper(),
            'linkedin': LinkedInScraper(),  # 🎉 NOUVEAU !
            'indeed': None  # À implémenter plus tard
        }
        
        # Initialisation conditionnelle des composants IA
        try:
            self.embedding_manager = EmbeddingManager()
            self.knowledge_base = KnowledgeBase()
            self.ai_features_enabled = True
            logger.info("🧠 Fonctionnalités IA activées")
        except Exception as e:
            self.embedding_manager = None
            self.knowledge_base = None
            self.ai_features_enabled = False
            logger.warning(f"⚠️ Fonctionnalités IA désactivées: {e}")
        
        self.last_scrape = None
        self.scraping_stats = {
            'total_jobs': 0,
            'last_update': None,
            'errors': [],
            'logs': [],
            'sources_stats': {}  # ✅ Stats par source
        }
    
    def add_log(self, message: str, level: str = 'info'):
        """Ajoute un log visible dans le frontend"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message
        }
        self.scraping_stats['logs'].append(log_entry)
        
        # Garder seulement les 100 derniers logs
        if len(self.scraping_stats['logs']) > 100:
            self.scraping_stats['logs'] = self.scraping_stats['logs'][-100:]
        
        # Log aussi dans le backend
        getattr(logger, level)(message)
    
    async def run_full_scrape(self, sources: List[str] = None) -> Dict[str, Any]:
        """Lance un scraping complet - Avec support LinkedIn"""
        if sources is None:
            sources = ['wttj', 'linkedin']  # ✅ LinkedIn par défaut
        
        self.add_log(f"🚀 Début du scraping pour : {sources}")
        start_time = datetime.now()
        all_jobs = []
        source_results = {}
        
        for source in sources:
            if source not in self.scrapers or self.scrapers[source] is None:
                self.add_log(f"❌ Scraper {source} non disponible", 'warning')
                continue
                
            try:
                self.add_log(f"📡 Scraping {source.upper()}...")
                scraper = self.scrapers[source]
                
                # Limite par source
                source_limit = min(
                    Config.MAX_JOBS_PER_SCRAPE // len(sources),  # Répartir équitablement
                    200  # Maximum par source
                )
                
                # ✅ Pas d'await ici car scrape_jobs est synchrone
                jobs = scraper.scrape_jobs(limit=source_limit)
                
                self.add_log(f"✅ {len(jobs)} offres récupérées de {source.upper()}")
                all_jobs.extend(jobs)
                
                # Stats par source
                source_results[source] = {
                    'jobs_found': len(jobs),
                    'success': True,
                    'duration': None  # À calculer si nécessaire
                }
                
                # Délai entre sources pour éviter la surcharge
                if len(sources) > 1:
                    await asyncio.sleep(3)
                
            except Exception as e:
                error_msg = f"Erreur scraping {source}: {str(e)}"
                self.add_log(error_msg, 'error')
                source_results[source] = {
                    'jobs_found': 0,
                    'success': False,
                    'error': str(e)
                }
                self.scraping_stats['errors'].append({
                    'source': source,
                    'error': error_msg,
                    'timestamp': datetime.now().isoformat()
                })
        
        # Traitement et stockage
        if all_jobs:
            self.add_log(f"🔄 Traitement de {len(all_jobs)} offres...")
            processed_jobs = await self.process_jobs(all_jobs)
            
            if self.ai_features_enabled:
                self.add_log("💾 Stockage avec IA...")
                await self.store_jobs(processed_jobs)
            else:
                self.add_log("💾 Stockage simple...")
                self.store_jobs_simple(processed_jobs)
        
        # Mise à jour des stats
        duration = (datetime.now() - start_time).total_seconds()
        self.scraping_stats.update({
            'total_jobs': len(all_jobs),
            'last_update': datetime.now().isoformat(),
            'duration_seconds': duration,
            'sources_processed': sources,
            'sources_stats': source_results,  # ✅ Détail par source
            'success': len(all_jobs) > 0
        })
        
        self.add_log(f"🎉 Scraping terminé : {len(all_jobs)} offres en {duration:.1f}s")
        
        # Sauvegarde du rapport
        self.save_scraping_report()
        
        return self.scraping_stats
    
    async def process_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Traite et nettoie les offres d'emploi - Version améliorée"""
        self.add_log(f"🔄 Traitement de {len(jobs)} offres...")
        
        processed = []
        source_counts = {}
        
        for i, job in enumerate(jobs):
            try:
                # Comptage par source
                source = job.get('source', 'unknown')
                source_counts[source] = source_counts.get(source, 0) + 1
                
                # Nettoyage et normalisation
                clean_job = {
                    'title': self.clean_text(job.get('title', '')),
                    'company': self.clean_text(job.get('company', '')),
                    'location': self.clean_text(job.get('location', '')),
                    'description': self.clean_text(job.get('description', '')),
                    'url': job.get('url', ''),
                    'source': source,
                    'scraped_at': datetime.now().isoformat(),
                    'hash_id': self.generate_job_hash(job)
                }
                
                # Enrichissement avec IA (si disponible)
                if self.ai_features_enabled:
                    clean_job.update({
                        'requirements': self.extract_requirements(job.get('description', '')),
                        'salary': self.extract_salary(job.get('description', '')),
                        'remote': self.detect_remote(job.get('description', '') + ' ' + job.get('title', '')),
                        'experience_level': self.detect_experience_level(job.get('title', '') + ' ' + job.get('description', '')),
                        'technologies': self.extract_technologies(job.get('description', '') + ' ' + job.get('title', '')),
                    })
                    
                    # Génération d'embedding conditionnelle
                    try:
                        full_text = f"{clean_job['title']} {clean_job['company']} {clean_job['description']}"
                        clean_job['embedding'] = await self.embedding_manager.generate_embedding(full_text)
                    except Exception as e:
                        logger.debug(f"Erreur embedding: {e}")
                        clean_job['embedding'] = []
                
                processed.append(clean_job)
                
                # Log de progression
                if (i + 1) % 10 == 0:
                    self.add_log(f"📊 Traité {i + 1}/{len(jobs)} offres...")
                
            except Exception as e:
                self.add_log(f"❌ Erreur traitement offre {i+1}: {e}", 'error')
                continue
        
        # Log du résumé par source
        for source, count in source_counts.items():
            self.add_log(f"📈 {source.upper()}: {count} offres traitées")
        
        self.add_log(f"✅ {len(processed)} offres traitées avec succès")
        return processed
    
    def store_jobs_simple(self, jobs: List[Dict]) -> None:
        """Stockage simple sans IA - Amélioré"""
        try:
            # Créer le dossier de données
            os.makedirs('./data/scraped', exist_ok=True)
            
            # Organiser par source
            jobs_by_source = {}
            for job in jobs:
                source = job.get('source', 'unknown')
                if source not in jobs_by_source:
                    jobs_by_source[source] = []
                jobs_by_source[source].append(job)
            
            # Sauvegarder par source
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            for source, source_jobs in jobs_by_source.items():
                filename = f"./data/scraped/{source}_jobs_{timestamp}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(source_jobs, f, indent=2, ensure_ascii=False)
                
                self.add_log(f"💾 {len(source_jobs)} offres {source.upper()} sauvegardées dans {filename}")
            
            # Sauvegarde globale
            global_filename = f"./data/scraped/all_jobs_{timestamp}.json"
            with open(global_filename, 'w', encoding='utf-8') as f:
                json.dump(jobs, f, indent=2, ensure_ascii=False)
            
            self.add_log(f"💾 {len(jobs)} offres totales sauvegardées dans {global_filename}")
            
        except Exception as e:
            self.add_log(f"❌ Erreur stockage: {e}", 'error')
    
    async def store_jobs(self, jobs: List[Dict]) -> None:
        """Stockage avec IA - Version corrigée"""
        if not self.ai_features_enabled:
            self.store_jobs_simple(jobs)
            return
        
        self.add_log(f"💾 Stockage avec IA de {len(jobs)} offres...")
        
        stored_count = 0
        source_stored = {}
        
        for job in jobs:
            try:
                source = job.get('source', 'unknown')
                
                if hasattr(self.knowledge_base, 'store_job'):
                    success = await self.knowledge_base.store_job(job)
                    if success:
                        stored_count += 1
                        source_stored[source] = source_stored.get(source, 0) + 1
                else:
                    self.add_log("⚠️ Méthode store_job non disponible", 'warning')
                    
            except Exception as e:
                self.add_log(f"❌ Erreur stockage offre {job.get('title', 'Unknown')}: {e}", 'error')
        
        # Log par source
        for source, count in source_stored.items():
            self.add_log(f"💾 {source.upper()}: {count} offres stockées")
        
        self.add_log(f"✅ {stored_count}/{len(jobs)} offres stockées avec succès")
    
    def save_scraping_report(self):
        """Sauvegarde un rapport de scraping détaillé"""
        try:
            os.makedirs('./data/reports', exist_ok=True)
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'stats': self.scraping_stats,
                'config': {
                    'ai_enabled': self.ai_features_enabled,
                    'sources_available': [name for name, scraper in self.scrapers.items() if scraper is not None],
                    'sources_configured': list(self.scrapers.keys()),
                    'max_jobs_per_scrape': getattr(Config, 'MAX_JOBS_PER_SCRAPE', 100)
                },
                'summary': {
                    'total_jobs_scraped': self.scraping_stats.get('total_jobs', 0),
                    'sources_used': self.scraping_stats.get('sources_processed', []),
                    'success_rate': len([s for s in self.scraping_stats.get('sources_stats', {}).values() if s.get('success', False)]),
                    'duration_minutes': round(self.scraping_stats.get('duration_seconds', 0) / 60, 2)
                }
            }
            
            filename = f"./data/reports/scraping_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📊 Rapport de scraping sauvegardé: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde rapport: {e}")
    
    def get_available_sources(self) -> List[str]:
        """Retourne la liste des sources de scraping disponibles"""
        return [name for name, scraper in self.scrapers.items() if scraper is not None]
    
    def get_sources_status(self) -> Dict[str, Any]:
        """Retourne le statut détaillé de chaque source"""
        status = {}
        
        for name, scraper in self.scrapers.items():
            if scraper is not None:
                status[name] = {
                    'available': True,
                    'name': scraper.name if hasattr(scraper, 'name') else name.upper(),
                    'last_scrape': None,  # À implémenter si nécessaire
                    'total_jobs_scraped': self.scraping_stats.get('sources_stats', {}).get(name, {}).get('jobs_found', 0)
                }
            else:
                status[name] = {
                    'available': False,
                    'name': name.upper(),
                    'reason': 'Scraper non implémenté'
                }
        
        return status
    
    # Méthodes utilitaires (inchangées mais optimisées)
    def clean_text(self, text: str) -> str:
        """Nettoie le texte des offres"""
        import re
        if not text:
            return ""
        
        # Supprimer HTML si présent
        text = re.sub(r'<[^>]+>', '', text)
        # Normaliser les espaces
        text = re.sub(r'\s+', ' ', text)
        # Supprimer caractères spéciaux problématiques
        text = re.sub(r'[^\w\s\-\.,;:!?()&@#%]', ' ', text)
        text = text.strip()
        
        return text[:5000]  # Limite de longueur
    
    def extract_requirements(self, description: str) -> List[str]:
        """Extrait les compétences requises - Version améliorée"""
        import re
        
        requirements = []
        description_lower = description.lower()
        
        # Patterns pour détecter les compétences
        patterns = [
            r'(?:compétences?|skills?|requis|required|exigé)[:\-\s]+(.*?)(?:\n|\.{2,}|;{2,})',
            r'(?:maîtrise|maîtriser|experience|expérience)[:\-\s]+(.*?)(?:\n|\.{2,}|;{2,})',
            r'(?:connaissances?|knowledge)[:\-\s]+(.*?)(?:\n|\.{2,}|;{2,})',
            r'(?:outils|tools)[:\-\s]+(.*?)(?:\n|\.{2,}|;{2,})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, description, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                # Séparer par virgules, points-virgules, etc.
                skills = re.split(r'[,;•\-\n]+', match)
                for skill in skills:
                    skill = skill.strip()
                    if skill and len(skill) > 2 and len(skill) < 100:
                        requirements.append(skill)
        
        # Nettoyer et dédupliquer
        requirements = list(set([req for req in requirements if req]))
        return requirements[:15]  # Limiter à 15 compétences
    
    def extract_salary(self, description: str) -> Dict[str, Any]:
        """Extrait les informations de salaire - Version améliorée"""
        import re
        
        # Patterns pour différents formats de salaire
        salary_patterns = [
            # Salaires en K€
            r'(\d+)k?\s*[-–à]\s*(\d+)k?\s*€',
            r'(\d+)\s*k€?\s*[-–à]\s*(\d+)\s*k€?',
            # Salaires complets
            r'(\d+\.?\d*)\s*[-–à]\s*(\d+\.?\d*)\s*€',
            r'(\d{3,6})\s*[-–à]\s*(\d{3,6})\s*euros?',
            # Salaire unique
            r'(\d+)\s*k€',
            r'(\d{3,6})\s*€',
            r'salaire\s*:?\s*(\d+\.?\d*)',
            # Formats anglais
            r'\$(\d+)k?\s*[-–]\s*\$?(\d+)k?',
        ]
        
        description_lower = description.lower()
        
        for pattern in salary_patterns:
            matches = re.finditer(pattern, description_lower, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                
                try:
                    if len(groups) >= 2 and groups[1]:
                        # Fourchette de salaire
                        min_sal = float(groups[0])
                        max_sal = float(groups[1])
                        
                        # Ajuster les unités (k€)
                        if 'k' in match.group(0).lower():
                            min_sal *= 1000
                            max_sal *= 1000
                        
                        return {
                            'found': True,
                            'text': match.group(0),
                            'min': int(min_sal),
                            'max': int(max_sal),
                            'currency': 'EUR'
                        }
                    
                    elif len(groups) >= 1:
                        # Salaire unique
                        salary = float(groups[0])
                        
                        if 'k' in match.group(0).lower():
                            salary *= 1000
                        
                        return {
                            'found': True,
                            'text': match.group(0),
                            'min': int(salary),
                            'max': int(salary),
                            'currency': 'EUR'
                        }
                        
                except ValueError:
                    continue
        
        return {'found': False, 'text': '', 'min': None, 'max': None, 'currency': None}
    
    def detect_remote(self, text: str) -> bool:
        """Détecte si le poste est en remote - Version améliorée"""
        remote_keywords = [
            'remote', 'télétravail', 'home office', 'distanciel', 'hybride',
            'travail à distance', 'full remote', 'partial remote', 'teletravail',
            'depuis chez vous', 'anywhere', 'nomade', 'distributed'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in remote_keywords)
    
    def detect_experience_level(self, text: str) -> str:
        """Détecte le niveau d'expérience requis - Version améliorée"""
        text_lower = text.lower()
        
        # Patterns pour senior
        senior_patterns = [
            'senior', 'lead', 'principal', 'architect', 'expert',
            '5+ ans', '7+ ans', '10+ ans', 'experienced', 'confirmé'
        ]
        
        # Patterns pour junior
        junior_patterns = [
            'junior', 'débutant', 'entry level', 'graduate', 'stagiaire',
            '0-2 ans', '1-2 ans', 'stage', 'alternance', 'apprenti'
        ]
        
        # Patterns pour lead/management
        lead_patterns = [
            'manager', 'chef', 'head of', 'director', 'responsable',
            'team lead', 'tech lead', 'engineering manager'
        ]
        
        if any(pattern in text_lower for pattern in lead_patterns):
            return 'lead'
        elif any(pattern in text_lower for pattern in senior_patterns):
            return 'senior'
        elif any(pattern in text_lower for pattern in junior_patterns):
            return 'junior'
        else:
            return 'mid'
    
    def extract_technologies(self, text: str) -> List[str]:
        """Extrait les technologies mentionnées - Version étendue"""
        tech_keywords = [
            # Langages de programmation
            'python', 'javascript', 'java', 'c++', 'c#', 'php', 'ruby', 'go',
            'rust', 'kotlin', 'swift', 'typescript', 'scala', 'r', 'matlab',
            
            # Frameworks web
            'react', 'vue', 'angular', 'node.js', 'express', 'django', 'flask',
            'spring', 'laravel', 'rails', 'nextjs', 'nuxt', 'svelte',
            
            # Bases de données
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
            'cassandra', 'dynamodb', 'oracle', 'sqlite',
            
            # Cloud et DevOps
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git',
            'terraform', 'ansible', 'linux', 'unix', 'nginx', 'apache',
            
            # Data Science & AI
            'tensorflow', 'pytorch', 'pandas', 'numpy', 'scikit-learn',
            'machine learning', 'deep learning', 'ai', 'data science',
            'tableau', 'power bi', 'spark', 'hadoop',
            
            # Mobile
            'ios', 'android', 'react native', 'flutter', 'xamarin',
            
            # Autres
            'html', 'css', 'sass', 'webpack', 'babel', 'graphql', 'rest api',
            'microservices', 'agile', 'scrum', 'devops', 'ci/cd'
        ]
        
        found_techs = []
        text_lower = text.lower()
        
        for tech in tech_keywords:
            if tech.lower() in text_lower:
                found_techs.append(tech)
        
        return list(set(found_techs))  # Dédupliquer
    
    def generate_job_hash(self, job: Dict) -> str:
        """Génère un hash unique pour l'offre"""
        import hashlib
        
        unique_string = f"{job.get('title', '')}{job.get('company', '')}{job.get('url', '')}"
        return hashlib.md5(unique_string.encode()).hexdigest()
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de scraping détaillées"""
        stats = {
            **self.scraping_stats,
            'available_scrapers': self.get_available_sources(),
            'scrapers_status': self.get_sources_status(),
            'ai_features_enabled': self.ai_features_enabled
        }
        
        # Ajouter les stats de la base de connaissances si disponible
        if self.ai_features_enabled and self.knowledge_base:
            try:
                stats['knowledge_base_stats'] = self.knowledge_base.get_stats()
            except Exception as e:
                logger.debug(f"Erreur récupération stats KB: {e}")
        
        return stats
    
    def get_logs(self) -> List[Dict]:
        """Retourne les logs pour le frontend"""
        return self.scraping_stats.get('logs', [])
    
    def clear_logs(self):
        """Efface les logs"""
        self.scraping_stats['logs'] = []
        self.add_log("🧹 Logs effacés")

# ==========================================
# MISE À JOUR DU TEMPLATE ADMIN
# ==========================================

# templates/admin/scraper_dashboard.html - Section à mettre à jour

"""
<!-- Sources de scraping -->
<div class="row mb-3">
    <div class="col-12">
        <label class="form-label">Sources de données</label>
        <div class="row">
            <div class="col-md-4">
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="wttj" checked>
                    <label class="form-check-label" for="wttj">
                        <strong>Welcome to the Jungle</strong>
                        <br><small class="text-muted">Offres tech et startup</small>
                    </label>
                </div>
            </div>
            <div class="col-md-4">
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="linkedin" checked>
                    <label class="form-check-label" for="linkedin">
                        <strong>LinkedIn Jobs</strong> ✨ NOUVEAU
                        <br><small class="text-muted">Offres professionnelles</small>
                    </label>
                </div>
            </div>
            <div class="col-md-4">
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="indeed" disabled>
                    <label class="form-check-label" for="indeed">
                        <strong>Indeed</strong>
                        <br><small class="text-muted">Bientôt disponible</small>
                    </label>
                </div>
            </div>
        </div>
    </div>
</div>
"""

# ==========================================
# TEST DU SYSTÈME COMPLET
# ==========================================

def test_multi_source_scraping():
    """Test du scraping multi-sources"""
    from models.scraper import ScrapingOrchestrator
    import asyncio
    
    async def run_test():
        orchestrator = ScrapingOrchestrator()
        
        # Test avec les deux sources
        print("🧪 Test scraping multi-sources...")
        stats = await orchestrator.run_full_scrape(['wttj', 'linkedin'])
        
        print(f"\n📊 RÉSULTATS:")
        print(f"Total offres: {stats.get('total_jobs', 0)}")
        print(f"Sources: {stats.get('sources_processed', [])}")
        
        for source, source_stats in stats.get('sources_stats', {}).items():
            print(f"{source.upper()}: {source_stats.get('jobs_found', 0)} offres")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_test())
    loop.close()

if __name__ == "__main__":
    test_multi_source_scraping()
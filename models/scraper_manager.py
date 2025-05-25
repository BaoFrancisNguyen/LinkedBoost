# models/scraper_manager.py - Gestionnaire de scraping avec Selenium
import asyncio
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from scrapers.wttj_scraper import WTTJScraper
from scrapers.linkedin_scraper import LinkedInScraper
from scrapers.indeed_scraper import IndeedScraper
from models.embeddings import EmbeddingManager
from models.knowledge_base import KnowledgeBase
from config import Config
import os
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScrapingManager:
    """Gestionnaire principal pour le scraping réel multi-sites"""
    
    def __init__(self):
        self.scrapers = {
            'wttj': WTTJScraper(),
            'linkedin': LinkedInScraper(),
            'indeed': IndeedScraper()
        }
        self.embedding_manager = EmbeddingManager()
        self.knowledge_base = KnowledgeBase()
        self.last_scrape = None
        self.scraping_stats = {
            'total_jobs': 0,
            'last_update': None,
            'errors': [],
            'success_rate': 0,
            'sources_stats': {}
        }
        
        # Configuration de credentials LinkedIn (si disponible)
        self.linkedin_credentials = {
            'email': os.environ.get('LINKEDIN_EMAIL', ''),
            'password': os.environ.get('LINKEDIN_PASSWORD', '')
        }
    
    async def run_full_scrape(self, sources: List[str] = None, 
                            max_jobs_per_source: int = None) -> Dict[str, Any]:
        """Lance un scraping complet de toutes les sources sélectionnées"""
        if sources is None:
            sources = ['wttj', 'indeed']  # LinkedIn optionnel (nécessite credentials)
        
        if max_jobs_per_source is None:
            max_jobs_per_source = Config.MAX_JOBS_PER_SCRAPE // len(sources)
        
        logger.info(f"🚀 Début du scraping réel pour : {sources}")
        start_time = datetime.now()
        all_jobs = []
        source_results = {}
        
        for source in sources:
            if source not in self.scrapers:
                logger.warning(f"❌ Scraper {source} non disponible")
                continue
                
            try:
                logger.info(f"📡 Scraping {source.upper()}...")
                scraper = self.scrapers[source]
                
                # Gestion spéciale pour LinkedIn (nécessite login)
                if source == 'linkedin':
                    if not self.linkedin_credentials['email']:
                        logger.warning("⚠️ LinkedIn: credentials manquants, passage au mode limité")
                        continue
                    
                    # Tentative de connexion LinkedIn
                    login_success = await scraper.login_linkedin(
                        self.linkedin_credentials['email'],
                        self.linkedin_credentials['password']
                    )
                    
                    if not login_success:
                        logger.error("❌ Échec connexion LinkedIn, passage à la source suivante")
                        source_results[source] = {
                            'jobs_count': 0,
                            'status': 'login_failed',
                            'error': 'Échec de connexion'
                        }
                        continue
                
                # Lancement du scraping
                jobs = await scraper.scrape_jobs(limit=max_jobs_per_source)
                
                logger.info(f"✅ {len(jobs)} offres récupérées de {source.upper()}")
                all_jobs.extend(jobs)
                
                source_results[source] = {
                    'jobs_count': len(jobs),
                    'status': 'success',
                    'sample_jobs': jobs[:3] if jobs else []
                }
                
                # Délai entre sources pour éviter la surcharge
                if source != sources[-1]:  # Pas de délai après la dernière source
                    delay = Config.REQUEST_DELAY * 5  # Délai plus long entre sources
                    logger.info(f"⏳ Attente {delay}s avant la source suivante...")
                    await asyncio.sleep(delay)
                
            except Exception as e:
                error_msg = f"Erreur scraping {source}: {str(e)}"
                logger.error(error_msg)
                
                source_results[source] = {
                    'jobs_count': 0,
                    'status': 'error',
                    'error': error_msg
                }
                
                self.scraping_stats['errors'].append({
                    'source': source,
                    'error': error_msg,
                    'timestamp': datetime.now().isoformat()
                })
        
        # Traitement et stockage des offres collectées
        processed_jobs = []
        if all_jobs:
            logger.info(f"🔄 Traitement de {len(all_jobs)} offres...")
            processed_jobs = await self.process_jobs(all_jobs)
            await self.store_jobs(processed_jobs)
        
        # Calcul des statistiques finales
        duration = (datetime.now() - start_time).total_seconds()
        success_rate = (len([r for r in source_results.values() if r['status'] == 'success']) / len(sources)) * 100
        
        self.scraping_stats.update({
            'total_jobs': len(processed_jobs),
            'last_update': datetime.now().isoformat(),
            'duration_seconds': duration,
            'success_rate': round(success_rate, 1),
            'sources_stats': source_results
        })
        
        logger.info(f"🎉 Scraping terminé : {len(processed_jobs)} offres traitées en {duration:.1f}s")
        
        # Sauvegarde des statistiques
        await self.save_scraping_report(all_jobs, processed_jobs, source_results)
        
        return self.scraping_stats
    
    async def process_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Traite et enrichit les offres d'emploi collectées"""
        logger.info(f"🔄 Traitement avancé de {len(jobs)} offres...")
        
        processed = []
        duplicates_removed = 0
        
        # Déduplication basée sur titre + entreprise
        seen_jobs = set()
        
        for job in jobs:
            try:
                # Nettoyage et normalisation de base
                clean_job = {
                    'title': self.clean_text(job.get('title', '')),
                    'company': self.clean_text(job.get('company', '')),
                    'location': self.clean_text(job.get('location', '')),
                    'description': self.clean_text(job.get('description', '')),
                    'url': job.get('url', ''),
                    'source': job.get('source', 'unknown'),
                    'scraped_at': datetime.now().isoformat()
                }
                
                # Vérification de déduplication
                job_signature = f"{clean_job['title'].lower()}_{clean_job['company'].lower()}"
                if job_signature in seen_jobs:
                    duplicates_removed += 1
                    continue
                seen_jobs.add(job_signature)
                
                # Enrichissement avancé
                clean_job.update(await self.enrich_job_data(job, clean_job))
                
                # Génération d'un hash unique
                clean_job['hash_id'] = self.generate_job_hash(clean_job)
                
                # Génération d'embedding pour le contenu complet
                if hasattr(self.embedding_manager, 'generate_embedding'):
                    full_text = f"{clean_job['title']} {clean_job['company']} {clean_job['description']}"
                    try:
                        embedding = await self.embedding_manager.generate_embedding(full_text)
                        clean_job['embedding'] = embedding
                    except Exception as e:
                        logger.debug(f"Erreur génération embedding: {e}")
                
                processed.append(clean_job)
                
            except Exception as e:
                logger.error(f"Erreur traitement offre: {e}")
                continue
        
        logger.info(f"✅ {len(processed)} offres traitées ({duplicates_removed} doublons supprimés)")
        return processed
    
    async def enrich_job_data(self, raw_job: Dict, clean_job: Dict) -> Dict[str, Any]:
        """Enrichissement avancé des données d'offres"""
        enrichment = {}
        
        # Extraction des compétences requises
        description = clean_job.get('description', '') + ' ' + raw_job.get('full_description', '')
        enrichment['requirements'] = self.extract_requirements(description)
        
        # Analyse du salaire
        salary_text = raw_job.get('salary', '') + ' ' + description
        enrichment['salary'] = self.extract_salary(salary_text)
        
        # Détection du remote
        remote_info = self.detect_remote_work(description + ' ' + clean_job['title'])
        enrichment['remote'] = remote_info['is_remote']
        enrichment['remote_details'] = remote_info['details']
        
        # Niveau d'expérience requis
        enrichment['experience_level'] = self.detect_experience_level(
            clean_job['title'] + ' ' + description
        )
        
        # Technologies extraites
        enrichment['technologies'] = self.extract_technologies(description)
        
        # Type de contrat
        enrichment['contract_type'] = raw_job.get('contract_type', self.detect_contract_type(description))
        
        # Avantages
        enrichment['benefits'] = raw_job.get('benefits', [])
        if isinstance(enrichment['benefits'], str):
            enrichment['benefits'] = [enrichment['benefits']]
        
        # Informations sur l'entreprise
        if 'company_info' in raw_job:
            enrichment['company_info'] = raw_job['company_info']
        
        # Score de qualité de l'offre
        enrichment['quality_score'] = self.calculate_job_quality_score(clean_job, enrichment)
        
        return enrichment
    
    def extract_requirements(self, description: str) -> List[str]:
        """Extraction intelligente des compétences requises"""
        import re
        
        requirements = []
        
        # Patterns pour identifier les sections de compétences
        skill_patterns = [
            r'(?:compétences?|skills?|requis|required|must have)[:\-\s]+(.*?)(?:\n\n|\.|;|$)',
            r'(?:profil recherché|candidat idéal)[:\-\s]+(.*?)(?:\n\n|\.|$)',
            r'(?:vous maîtrisez|experience with)[:\-\s]+(.*?)(?:\n\n|\.|$)',
            r'(?:technologies?|outils?)[:\-\s]+(.*?)(?:\n\n|\.|$)'
        ]
        
        for pattern in skill_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE | re.DOTALL)
            for match in matches:
                # Découpage et nettoyage
                skills = re.split(r'[,;\n\-•]', match)
                for skill in skills:
                    clean_skill = skill.strip()
                    if len(clean_skill) > 2 and len(clean_skill) < 50:
                        requirements.append(clean_skill)
        
        # Déduplication et limitation
        return list(set(requirements))[:15]
    
    def extract_salary(self, text: str) -> Dict[str, Any]:
        """Extraction avancée des informations de salaire"""
        import re
        
        salary_patterns = [
            r'(\d+)k?\s*[-–]\s*(\d+)k?\s*€',
            r'(\d+)\s*k€\s*[-–]\s*(\d+)\s*k€',
            r'(\d+)\s*000\s*[-–]\s*(\d+)\s*000\s*€',
            r'salaire\s*:?\s*(\d+)\s*k€?',
            r'rémunération\s*:?\s*(\d+)\s*k€?',
            r'package\s*:?\s*(\d+)\s*k€?',
            r'(\d+)\s*€\s*brut'
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    min_val = int(groups[0])
                    max_val = int(groups[1])
                    
                    # Ajustement si valeurs en k
                    if 'k' in match.group(0).lower() or min_val < 200:
                        min_val *= 1000
                        max_val *= 1000
                    
                    return {
                        'found': True,
                        'min': min_val,
                        'max': max_val,
                        'text': match.group(0),
                        'currency': 'EUR'
                    }
                else:
                    val = int(groups[0])
                    if 'k' in match.group(0).lower() or val < 200:
                        val *= 1000
                    
                    return {
                        'found': True,
                        'amount': val,
                        'text': match.group(0),
                        'currency': 'EUR'
                    }
        
        return {'found': False, 'text': '', 'min': None, 'max': None}
    
    def detect_remote_work(self, text: str) -> Dict[str, Any]:
        """Détection avancée des modalités de télétravail"""
        text_lower = text.lower()
        
        remote_indicators = {
            'full_remote': ['100% remote', 'full remote', 'télétravail complet', 'entièrement à distance', 'remote only'],
            'hybrid': ['hybride', 'télétravail partiel', 'flex office', '2-3 jours', 'partiellement remote'],
            'flexible': ['télétravail possible', 'remote ponctuel', 'arrangements flexibles'],
            'no_remote': ['présentiel obligatoire', 'sur site uniquement', 'pas de télétravail']
        }
        
        detected_type = 'unknown'
        confidence = 0.0
        keywords_found = []
        
        for work_type, keywords in remote_indicators.items():
            found_keywords = [kw for kw in keywords if kw in text_lower]
            if found_keywords:
                detected_type = work_type
                keywords_found = found_keywords
                confidence = len(found_keywords) / len(keywords)
                break
        
        is_remote = detected_type in ['full_remote', 'hybrid', 'flexible']
        
        return {
            'is_remote': is_remote,
            'details': {
                'type': detected_type,
                'confidence': confidence,
                'keywords_found': keywords_found
            }
        }
    
    def detect_experience_level(self, text: str) -> str:
        """Classification du niveau d'expérience requis"""
        text_lower = text.lower()
        
        # Patterns avancés pour chaque niveau
        patterns = {
            'junior': [
                r'junior', r'débutant', r'[0-2]\s*an', r'stage', r'alternance',
                r'first job', r'graduate', r'entry level', r'moins de 3 ans'
            ],
            'senior': [
                r'senior', r'lead', r'principal', r'architect', r'[5-9]\+?\s*an',
                r'expert', r'[1-9][0-9]\+?\s*an', r'plus de 5 ans', r'expérimenté'
            ],
            'mid': [
                r'[3-5]\s*an', r'confirmé', r'experienced', r'3 à 5 ans'
            ]
        }
        
        scores = {}
        for level, level_patterns in patterns.items():
            score = 0
            for pattern in level_patterns:
                if re.search(pattern, text_lower):
                    score += 1
            scores[level] = score
        
        # Retourner le niveau avec le score le plus élevé
        if max(scores.values()) == 0:
            return 'mid'  # Par défaut
        
        return max(scores, key=scores.get)
    
    def extract_technologies(self, description: str) -> List[str]:
        """Extraction des technologies avec scoring avancé"""
        tech_database = {
            # Langages de programmation
            'python': ['python', 'py', 'django', 'flask', 'fastapi'],
            'javascript': ['javascript', 'js', 'node.js', 'nodejs', 'react', 'vue', 'angular'],
            'java': ['java', 'spring', 'spring boot'],
            'php': ['php', 'laravel', 'symfony'],
            'c#': ['c#', 'csharp', '.net', 'dotnet'],
            'go': ['golang', 'go'],
            'rust': ['rust'],
            'typescript': ['typescript', 'ts'],
            
            # Bases de données
            'postgresql': ['postgresql', 'postgres', 'psql'],
            'mysql': ['mysql'],
            'mongodb': ['mongodb', 'mongo'],
            'redis': ['redis'],
            'elasticsearch': ['elasticsearch', 'elastic'],
            
            # Cloud et DevOps
            'aws': ['aws', 'amazon web services'],
            'azure': ['azure', 'microsoft azure'],
            'gcp': ['gcp', 'google cloud'],
            'docker': ['docker', 'containerization'],
            'kubernetes': ['kubernetes', 'k8s'],
            'jenkins': ['jenkins'],
            'terraform': ['terraform'],
            
            # Frontend
            'react': ['react', 'reactjs'],
            'vue': ['vue', 'vuejs'],
            'angular': ['angular', 'angularjs'],
            
            # Data Science
            'tensorflow': ['tensorflow', 'tf'],
            'pytorch': ['pytorch'],
            'pandas': ['pandas'],
            'numpy': ['numpy'],
            'scikit-learn': ['scikit-learn', 'sklearn']
        }
        
        found_technologies = []
        description_lower = description.lower()
        
        for tech_name, variations in tech_database.items():
            for variation in variations:
                if variation in description_lower:
                    found_technologies.append(tech_name)
                    break
        
        return list(set(found_technologies))
    
    def detect_contract_type(self, description: str) -> str:
        """Détection du type de contrat"""
        text_lower = description.lower()
        
        contract_patterns = {
            'CDI': ['cdi', 'contrat à durée indéterminée', 'permanent'],
            'CDD': ['cdd', 'contrat à durée déterminée', 'temporary'],
            'freelance': ['freelance', 'indépendant', 'consultant', 'mission'],
            'stage': ['stage', 'internship', 'stagiaire'],
            'alternance': ['alternance', 'apprentissage', 'contrat pro']
        }
        
        for contract_type, patterns in contract_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                return contract_type
        
        return 'CDI'  # Par défaut
    
    def calculate_job_quality_score(self, job: Dict, enrichment: Dict) -> float:
        """Calcule un score de qualité pour l'offre"""
        score = 0.0
        
        # Description détaillée (+2 points)
        if len(job.get('description', '')) > 200:
            score += 2.0
        
        # Salaire mentionné (+1.5 points)
        if enrichment.get('salary', {}).get('found', False):
            score += 1.5
        
        # Technologies spécifiées (+1 point)
        if len(enrichment.get('technologies', [])) > 0:
            score += 1.0
        
        # Compétences détaillées (+1 point)
        if len(enrichment.get('requirements', [])) > 3:
            score += 1.0
        
        # Informations remote claires (+0.5 points)
        if enrichment.get('remote_details', {}).get('confidence', 0) > 0.5:
            score += 0.5
        
        # Localisation précise (+0.5 points)
        if job.get('location') and len(job['location']) > 5:
            score += 0.5
        
        # Avantages mentionnés (+0.5 points)
        if len(enrichment.get('benefits', [])) > 0:
            score += 0.5
        
        return min(score, 10.0)  # Score maximum de 10
    
    def clean_text(self, text: str) -> str:
        """Nettoyage avancé du texte"""
        import re
        if not text:
            return ""
        
        # Suppression HTML et caractères spéciaux
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\-\.,;:!?()\[\]\'\"€]', ' ', text)
        text = text.strip()
        
        return text[:10000]  # Limite de longueur
    
    def generate_job_hash(self, job: Dict) -> str:
        """Génère un hash unique pour l'offre"""
        import hashlib
        
        unique_string = f"{job.get('title', '')}{job.get('company', '')}{job.get('source', '')}"
        return hashlib.md5(unique_string.encode()).hexdigest()
    
    async def store_jobs(self, jobs: List[Dict]) -> None:
        """Stockage des offres dans la base de connaissances"""
        logger.info(f"💾 Stockage de {len(jobs)} offres...")
        
        stored_count = 0
        error_count = 0
        
        for job in jobs:
            try:
                success = await self.knowledge_base.store_job(job)
                if success:
                    stored_count += 1
                else:
                    logger.debug(f"Offre déjà existante: {job.get('title', 'Unknown')}")
            except Exception as e:
                error_count += 1
                logger.error(f"Erreur stockage offre {job.get('title', 'Unknown')}: {e}")
        
        logger.info(f"✅ Stockage terminé: {stored_count} nouvelles offres, {error_count} erreurs")
    
    async def save_scraping_report(self, raw_jobs: List[Dict], 
                                 processed_jobs: List[Dict], 
                                 source_results: Dict[str, Any]) -> None:
        """Sauvegarde un rapport détaillé du scraping"""
        try:
            os.makedirs("data/reports", exist_ok=True)
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'raw_jobs_collected': len(raw_jobs),
                    'processed_jobs': len(processed_jobs),
                    'sources_attempted': list(source_results.keys()),
                    'successful_sources': [k for k, v in source_results.items() if v['status'] == 'success'],
                    'total_duration': self.scraping_stats.get('duration_seconds', 0)
                },
                'source_details': source_results,
                'quality_analysis': self.analyze_job_quality(processed_jobs),
                'technology_trends': self.analyze_technology_trends(processed_jobs),
                'sample_jobs': processed_jobs[:5] if processed_jobs else []
            }
            
            filename = f"data/reports/scraping_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📊 Rapport sauvegardé: {filename}")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde rapport: {e}")
    
    def analyze_job_quality(self, jobs: List[Dict]) -> Dict[str, Any]:
        """Analyse la qualité des offres collectées"""
        if not jobs:
            return {}
        
        quality_scores = [job.get('quality_score', 0) for job in jobs]
        
        return {
            'average_quality': sum(quality_scores) / len(quality_scores),
            'high_quality_jobs': len([s for s in quality_scores if s >= 7]),
            'jobs_with_salary': len([j for j in jobs if j.get('salary', {}).get('found', False)]),
            'remote_jobs': len([j for j in jobs if j.get('remote', False)]),
            'jobs_with_technologies': len([j for j in jobs if j.get('technologies', [])])
        }
    
    def analyze_technology_trends(self, jobs: List[Dict]) -> Dict[str, int]:
        """Analyse les tendances technologiques"""
        tech_count = {}
        
        for job in jobs:
            technologies = job.get('technologies', [])
            for tech in technologies:
                tech_count[tech] = tech_count.get(tech, 0) + 1
        
        # Retourner les 15 technologies les plus demandées
        return dict(sorted(tech_count.items(), key=lambda x: x[1], reverse=True)[:15])
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques complètes du scraping"""
        base_stats = {
            **self.scraping_stats,
            'available_scrapers': list(self.scrapers.keys()),
            'linkedin_configured': bool(self.linkedin_credentials['email']),
            'last_scrape_time': self.last_scrape
        }
        
        # Ajouter les stats de la base de connaissances
        try:
            kb_stats = self.knowledge_base.get_stats()
            base_stats['knowledge_base_stats'] = kb_stats
        except Exception as e:
            base_stats['knowledge_base_error'] = str(e)
        
        return base_stats
    
    async def test_scrapers(self) -> Dict[str, Any]:
        """Test de connectivité et fonctionnement des scrapers"""
        results = {}
        
        for name, scraper in self.scrapers.items():
            try:
                logger.info(f"🧪 Test du scraper {name.upper()}...")
                
                if name == 'linkedin' and not self.linkedin_credentials['email']:
                    results[name] = {
                        'status': 'skipped',
                        'reason': 'Credentials manquants'
                    }
                    continue
                
                # Test avec limite très faible
                test_jobs = await scraper.scrape_jobs(limit=2)
                
                results[name] = {
                    'status': 'success' if test_jobs else 'no_results',
                    'jobs_found': len(test_jobs),
                    'sample_job': test_jobs[0] if test_jobs else None
                }
                
            except Exception as e:
                results[name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return results
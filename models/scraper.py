# models/scraper.py - Version mise à jour avec support Selenium
import asyncio
import time
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScrapingOrchestrator:
    """Orchestrateur principal pour le scraping avec support Selenium"""
    
    def __init__(self):
        self.scrapers = {}
        self.last_scrape = None
        self.scraping_stats = {
            'total_jobs': 0,
            'last_update': None,
            'errors': [],
            'sources': {},
            'selenium_available': False
        }
        
        # Initialisation des scrapers disponibles
        self.initialize_scrapers()
    
    def initialize_scrapers(self):
        """Initialise les scrapers disponibles avec détection automatique"""
        scrapers_initialized = []
        
        # 1. Tentative d'initialisation du scraper WTTJ avec Selenium
        try:
            from scrapers.wttj_scraper import create_wttj_scraper
            wttj_scraper = create_wttj_scraper()
            self.scrapers['wttj'] = wttj_scraper
            
            # Vérifier le type de scraper utilisé
            scraper_type = type(wttj_scraper).__name__
            if 'Fallback' in scraper_type:
                logger.info("✅ Scraper WTTJ initialisé (mode simulation)")
                self.scraping_stats['selenium_available'] = False
            else:
                logger.info("✅ Scraper WTTJ initialisé (Selenium activé)")
                self.scraping_stats['selenium_available'] = True
            
            scrapers_initialized.append('wttj')
            
        except ImportError as e:
            logger.warning(f"⚠️ Import scraper WTTJ échoué: {e}")
            # Fallback vers le scraper simple
            try:
                self.scrapers['wttj'] = SimpleWTTJScraper()
                scrapers_initialized.append('wttj (simple)')
                logger.info("✅ Scraper WTTJ simple activé")
            except Exception as e2:
                logger.error(f"❌ Impossible d'initialiser le scraper WTTJ: {e2}")
        
        except Exception as e:
            logger.error(f"❌ Erreur initialisation scraper WTTJ: {e}")
        
        # 2. Autres scrapers (à ajouter plus tard)
        # self.initialize_linkedin_scraper()
        # self.initialize_indeed_scraper()
        
        # Résumé de l'initialisation
        if scrapers_initialized:
            logger.info(f"📡 Scrapers disponibles: {scrapers_initialized}")
        else:
            logger.warning("⚠️ Aucun scraper disponible!")
    
    async def run_full_scrape(self, sources: List[str] = None) -> Dict[str, Any]:
        """Lance un scraping complet de toutes les sources"""
        if sources is None:
            sources = list(self.scrapers.keys())
        
        if not sources:
            logger.warning("⚠️ Aucune source de scraping spécifiée")
            return {'total_jobs': 0, 'error': 'Aucune source disponible'}
        
        logger.info(f"🚀 Début du scraping pour : {sources}")
        start_time = datetime.now()
        all_jobs = []
        
        for source in sources:
            if source not in self.scrapers:
                logger.warning(f"❌ Scraper {source} non disponible")
                self.scraping_stats['errors'].append({
                    'source': source,
                    'error': f'Scraper {source} non configuré',
                    'timestamp': datetime.now().isoformat()
                })
                continue
                
            try:
                logger.info(f"📡 Scraping {source}...")
                scraper = self.scrapers[source]
                
                # Scraping avec gestion d'erreur spécifique
                jobs = await scraper.scrape_jobs(limit=Config.MAX_JOBS_PER_SCRAPE)
                
                logger.info(f"✅ {len(jobs)} offres récupérées de {source}")
                all_jobs.extend(jobs)
                
                # Mise à jour des stats par source
                self.scraping_stats['sources'][source] = {
                    'jobs_count': len(jobs),
                    'last_scrape': datetime.now().isoformat(),
                    'scraper_type': type(scraper).__name__
                }
                
                # Délai entre sources pour éviter la surcharge
                if len(sources) > 1:
                    await asyncio.sleep(Config.REQUEST_DELAY * 2)
                
            except Exception as e:
                error_msg = f"Erreur scraping {source}: {str(e)}"
                logger.error(error_msg)
                self.scraping_stats['errors'].append({
                    'source': source,
                    'error': error_msg,
                    'timestamp': datetime.now().isoformat()
                })
        
        # Traitement et stockage des offres collectées
        if all_jobs:
            logger.info(f"🔄 Traitement de {len(all_jobs)} offres collectées...")
            processed_jobs = await self.process_jobs(all_jobs)
            await self.store_jobs(processed_jobs)
        else:
            logger.warning("⚠️ Aucune offre collectée")
        
        # Mise à jour des statistiques finales
        self.scraping_stats.update({
            'total_jobs': len(all_jobs),
            'last_update': datetime.now().isoformat(),
            'duration_seconds': (datetime.now() - start_time).total_seconds(),
            'success_rate': (len(all_jobs) / max(sum(len(self.scrapers) for _ in sources), 1)) * 100
        })
        
        logger.info(f"🎉 Scraping terminé : {len(all_jobs)} offres en {self.scraping_stats['duration_seconds']:.1f}s")
        return self.scraping_stats
    
    async def process_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Traite et enrichit les offres d'emploi"""
        logger.info(f"🔄 Traitement de {len(jobs)} offres...")
        
        processed = []
        for i, job in enumerate(jobs):
            try:
                # Nettoyage et normalisation
                clean_job = {
                    'title': self.clean_text(job.get('title', '')),
                    'company': self.clean_text(job.get('company', '')),
                    'location': self.clean_text(job.get('location', '')),
                    'description': self.clean_text(job.get('description', '')),
                    'contract_type': job.get('contract_type', 'CDI'),
                    'url': job.get('url', ''),
                    'source': job.get('source', 'unknown'),
                    'scraped_at': datetime.now().isoformat(),
                    'hash_id': self.generate_job_hash(job)
                }
                
                # Enrichissement avec analyse de contenu
                if clean_job['description']:
                    clean_job.update({
                        'requirements': self.extract_requirements(clean_job['description']),
                        'salary': self.extract_salary(clean_job['description']),
                        'remote': self.detect_remote(clean_job['description'] + ' ' + clean_job['title']),
                        'experience_level': self.detect_experience_level(clean_job['title'] + ' ' + clean_job['description']),
                        'technologies': self.extract_technologies(clean_job['description']),
                        'benefits': self.extract_benefits(clean_job['description'])
                    })
                
                # Validation des données essentielles
                if clean_job['title'] and clean_job['company']:
                    processed.append(clean_job)
                    if i < 3:  # Log des premières offres pour debug
                        logger.debug(f"✅ Offre traitée: {clean_job['title']} chez {clean_job['company']}")
                else:
                    logger.warning(f"⚠️ Offre ignorée (données manquantes): {job}")
                
            except Exception as e:
                logger.error(f"❌ Erreur traitement offre: {e}")
                continue
        
        logger.info(f"✅ {len(processed)} offres traitées avec succès")
        return processed
    
    def clean_text(self, text: str) -> str:
        """Nettoie et normalise le texte"""
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
            r'(?:compétences?|skills?|requis|required|prerequisites)[:\-\s]+(.*?)(?:\n|\.|;|Profil|Formation)',
            r'(?:maîtrise|expérience|expertise)[:\-\s]+(.*?)(?:\n|\.|;)',
            r'(?:vous maîtrisez|tu maîtrises)[:\-\s]+(.*?)(?:\n|\.|;)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, description, re.IGNORECASE | re.DOTALL)
            for match in matches:
                # Découpage par virgules/points/tirets
                skills = re.split(r'[,;\-•]+', match)
                requirements.extend([skill.strip() for skill in skills if skill.strip() and len(skill.strip()) > 2])
        
        # Filtrage et dédoublonnage
        unique_requirements = []
        for req in requirements:
            req_clean = req.lower().strip()
            if req_clean not in [r.lower() for r in unique_requirements] and len(req) < 100:
                unique_requirements.append(req.strip())
        
        return unique_requirements[:15]  # Max 15 compétences
    
    def extract_salary(self, description: str) -> Dict[str, Any]:
        """Extrait les informations de salaire avec patterns avancés"""
        import re
        
        salary_patterns = [
            r'(\d+)k?\s*[-–à]\s*(\d+)k?\s*€?\s*(?:brut|net)?',
            r'(\d+)\s*k€?\s*(?:brut|net)?(?:\s*(?:par|\/)\s*an)?',
            r'salaire[:\s]*(\d+)[-–](\d+)\s*k€?',
            r'rémunération[:\s]*(\d+)[-–](\d+)\s*k€?',
            r'package[:\s]*(\d+)[-–](\d+)\s*k€?',
            r'(\d+)\s*000\s*[-–]\s*(\d+)\s*000\s*€'
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    min_sal = int(groups[0]) * (1000 if 'k' in match.group(0).lower() or len(groups[0]) <= 3 else 1)
                    max_sal = int(groups[1]) * (1000 if 'k' in match.group(0).lower() or len(groups[1]) <= 3 else 1)
                    
                    return {
                        'found': True,
                        'text': match.group(0),
                        'min': min_sal,
                        'max': max_sal,
                        'currency': 'EUR'
                    }
                else:
                    sal = int(groups[0]) * (1000 if 'k' in match.group(0).lower() or len(groups[0]) <= 3 else 1)
                    return {
                        'found': True,
                        'text': match.group(0),
                        'amount': sal,
                        'currency': 'EUR'
                    }
        
        return {'found': False, 'text': '', 'min': None, 'max': None}
    
    def detect_remote(self, text: str) -> bool:
        """Détecte les modalités de travail à distance"""
        remote_keywords = [
            'remote', 'télétravail', 'home office', 'distanciel', 'hybride',
            '100% remote', 'full remote', 'partiellement remote', 'flex office'
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in remote_keywords)
    
    def detect_experience_level(self, text: str) -> str:
        """Détecte le niveau d'expérience avec patterns avancés"""
        text_lower = text.lower()
        
        # Patterns senior
        senior_patterns = [
            'senior', 'lead', 'principal', 'architect', 'expert', 'confirmé',
            r'[5-9]\+?\s*ans?', r'[1-9][0-9]\+?\s*ans?', 'expérimenté'
        ]
        
        # Patterns junior
        junior_patterns = [
            'junior', 'débutant', 'entry level', 'graduate', 'stage', 'alternance',
            r'0[-\s]?[12]?\s*ans?', 'first job', 'sortie d\'école'
        ]
        
        # Patterns mid-level
        mid_patterns = [
            r'[23456]\s*[-\s]\s*[456789]\s*ans?', 'intermédiaire', 'mid-level',
            r'[234]\+?\s*ans?'
        ]
        
        # Scoring par catégorie
        import re
        senior_score = sum(1 for pattern in senior_patterns if re.search(pattern, text_lower))
        junior_score = sum(1 for pattern in junior_patterns if re.search(pattern, text_lower))
        mid_score = sum(1 for pattern in mid_patterns if re.search(pattern, text_lower))
        
        if senior_score > max(junior_score, mid_score):
            return 'senior'
        elif junior_score > mid_score:
            return 'junior'
        else:
            return 'mid'
    
    def extract_technologies(self, description: str) -> List[str]:
        """Extrait les technologies avec reconnaissance avancée"""
        # Base de technologies étendue
        tech_keywords = {
            # Langages
            'python', 'javascript', 'typescript', 'java', 'go', 'rust', 'php', 'ruby',
            'c++', 'c#', 'scala', 'kotlin', 'swift', 'dart', 'r', 'matlab',
            
            # Frameworks Frontend
            'react', 'vue', 'vue.js', 'angular', 'svelte', 'next.js', 'nuxt.js',
            'jquery', 'bootstrap', 'tailwind', 'material-ui',
            
            # Frameworks Backend
            'django', 'flask', 'fastapi', 'spring', 'laravel', 'node.js', 'express',
            'nestjs', 'rails', 'symfony', 'asp.net',
            
            # Bases de données
            'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'sqlite',
            'oracle', 'cassandra', 'neo4j', 'dynamodb', 'firebase', 'supabase',
            
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible',
            'jenkins', 'gitlab', 'github', 'circleci', 'vercel', 'netlify',
            
            # Data & ML
            'pandas', 'numpy', 'tensorflow', 'pytorch', 'scikit-learn', 'spark',
            'hadoop', 'kafka', 'airflow', 'dbt', 'looker', 'tableau', 'powerbi',
            
            # Outils
            'git', 'jira', 'confluence', 'slack', 'notion', 'figma', 'adobe'
        }
        
        found_techs = []
        description_lower = description.lower()
        
        for tech in tech_keywords:
            # Recherche exacte avec délimiteurs de mots
            import re
            if re.search(r'\b' + re.escape(tech) + r'\b', description_lower):
                found_techs.append(tech)
        
        return found_techs
    
    def extract_benefits(self, description: str) -> List[str]:
        """Extrait les avantages proposés"""
        benefits_keywords = [
            'télétravail', 'remote', 'horaires flexibles', 'flex time',
            'mutuelle', 'assurance santé', 'tickets restaurant', 'tr',
            'participation', 'intéressement', 'prime', 'bonus',
            'formation', 'certification', 'conférence', 'budget formation',
            'congés', 'rtt', 'vacances', 'cp',
            'sport', 'salle de sport', 'vélo', 'transport',
            'afterwork', 'team building', 'séminaire'
        ]
        
        found_benefits = []
        description_lower = description.lower()
        
        for benefit in benefits_keywords:
            if benefit in description_lower:
                found_benefits.append(benefit)
        
        return found_benefits
    
    def generate_job_hash(self, job: Dict) -> str:
        """Génère un hash unique pour l'offre"""
        import hashlib
        
        # Utiliser titre + entreprise + URL pour l'unicité
        unique_string = f"{job.get('title', '')}{job.get('company', '')}{job.get('url', '')}"
        return hashlib.md5(unique_string.encode()).hexdigest()
    
    async def store_jobs(self, jobs: List[Dict]) -> None:
        """Stocke les offres dans la base de connaissances"""
        logger.info(f"💾 Stockage de {len(jobs)} offres...")
        
        try:
            # Import conditionnel de la base de connaissances
            from models.knowledge_base import KnowledgeBase
            kb = KnowledgeBase()
            
            stored_count = 0
            for job in jobs:
                try:
                    success = await kb.store_job(job)
                    if success:
                        stored_count += 1
                except Exception as e:
                    logger.error(f"Erreur stockage offre {job.get('title', 'Unknown')}: {e}")
            
            logger.info(f"✅ Stockage terminé : {stored_count}/{len(jobs)} offres stockées")
            
        except ImportError:
            logger.warning("⚠️ Base de connaissances non disponible, stockage ignoré")
        except Exception as e:
            logger.error(f"❌ Erreur lors du stockage: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques complètes de scraping"""
        return {
            **self.scraping_stats,
            'available_scrapers': list(self.scrapers.keys()),
            'scraping_enabled': len(self.scrapers) > 0,
            'selenium_status': self.scraping_stats.get('selenium_available', False),
            'last_scrape_time': self.last_scrape.isoformat() if self.last_scrape else None
        }
    
    def get_scraper_info(self, source: str) -> Dict[str, Any]:
        """Retourne les informations sur un scraper spécifique"""
        if source not in self.scrapers:
            return {'available': False, 'error': 'Scraper non configuré'}
        
        scraper = self.scrapers[source]
        return {
            'available': True,
            'name': getattr(scraper, 'name', source),
            'type': type(scraper).__name__,
            'selenium_based': 'Selenium' in type(scraper).__name__,
            'last_stats': self.scraping_stats.get('sources', {}).get(source, {})
        }


# Scraper simple de fallback (pour compatibilité)
class SimpleWTTJScraper:
    """Scraper de fallback avec données simulées réalistes"""
    
    def __init__(self):
        self.name = 'Welcome to the Jungle (Simulation)'
    
    async def scrape_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Génère des données simulées réalistes"""
        logger.info(f"🎭 Génération de {min(limit, 25)} offres simulées...")
        
        # Données d'entreprises françaises réelles
        companies = [
            "Aircall", "BlaBlaCar", "Doctolib", "Criteo", "Deezer",
            "Leboncoin", "Qonto", "Alan", "BackMarket", "Contentsquare",
            "Mirakl", "Algolia", "Datadog", "Dashlane", "Evaneos"
        ]
        
        titles = [
            "Développeur Full Stack Senior", "Data Scientist", "Product Manager",
            "Développeur Frontend React", "DevOps Engineer", "UX/UI Designer",
            "Backend Developer Python", "Machine Learning Engineer", "Scrum Master",
            "Lead Developer", "QA Engineer", "Business Analyst"
        ]
        
        locations = [
            "Paris", "Lyon", "Toulouse", "Nantes", "Bordeaux", 
            "Lille", "Marseille", "Remote", "Paris (Hybrid)"
        ]
        
        jobs = []
        for i in range(min(limit, 25)):
            company = companies[i % len(companies)]
            title = titles[i % len(titles)]
            location = locations[i % len(locations)]
            
            job = {
                'title': title,
                'company': company,
                'location': location,
                'description': self.generate_realistic_description(title, company),
                'url': f"https://www.welcometothejungle.com/fr/jobs/sim_{company.lower()}_{i}",
                'source': 'wttj',
                'contract_type': 'CDI',
                'scraped_at': time.time()
            }
            jobs.append(job)
            
            # Petit délai pour simuler le scraping
            await asyncio.sleep(0.1)
        
        logger.info(f"✅ {len(jobs)} offres simulées générées")
        return jobs
    
    def generate_realistic_description(self, title: str, company: str) -> str:
        """Génère une description réaliste selon le poste"""
        
        tech_stacks = {
            'Frontend': 'React, TypeScript, CSS3, Jest, Webpack',
            'Backend': 'Python, Django, PostgreSQL, Redis, Docker',
            'Full Stack': 'React, Node.js, MongoDB, AWS, Git',
            'Data': 'Python, Pandas, TensorFlow, SQL, Jupyter',
            'DevOps': 'Kubernetes, Terraform, AWS, Jenkins, Monitoring',
            'Mobile': 'React Native, Swift, Kotlin, Firebase'
        }
        
        # Déterminer la stack selon le titre
        stack = 'Full Stack'  # Défaut
        for key in tech_stacks:
            if key.lower() in title.lower():
                stack = key
                break
        
        technologies = tech_stacks[stack]
        
        return f"""
{company} recherche un(e) {title} pour rejoindre notre équipe en pleine croissance.

🎯 Missions principales :
• Développement et maintenance des applications
• Collaboration avec les équipes produit et design  
• Participation aux décisions techniques et architecturales
• Code review et mentoring des développeurs junior
• Amélioration continue des processus et performances

🔧 Stack technique :
{technologies}

💡 Profil recherché :
• 3+ années d'expérience sur des technologies similaires
• Maîtrise des méthodologies agiles (Scrum/Kanban)
• Anglais technique courant
• Esprit d'équipe et autonomie
• Passion pour la tech et l'innovation

🎁 Ce qu'on propose :
• Télétravail flexible (2-3 jours/semaine)
• Formation continue et budget conférences
• Mutuelle premium et tickets restaurant
• Stock-options et participation aux bénéfices
• Environnement stimulant dans une scale-up en croissance

Poste en CDI basé à Paris avec possibilité de remote partiel.
Rémunération selon profil et expérience.
        """.strip()

# Import time pour le fallback
import time
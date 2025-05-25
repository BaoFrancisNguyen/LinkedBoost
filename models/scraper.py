# models/scraper.py - Orchestrateur de scraping RÉEL complet
import asyncio
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
import json

# Import des scrapers RÉELS avec fallback de création automatique
def ensure_scrapers_exist():
    """S'assure que les scrapers existent, les crée sinon"""
    scrapers_dir = 'scrapers'
    
    if not os.path.exists(scrapers_dir):
        os.makedirs(scrapers_dir, exist_ok=True)
    
    # Créer __init__.py si manquant
    init_file = os.path.join(scrapers_dir, '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write('# scrapers package\n')
    
    # Créer base_scraper.py si manquant
    base_file = os.path.join(scrapers_dir, 'base_scraper.py')
    if not os.path.exists(base_file):
        base_content = '''# scrapers/base_scraper.py
import asyncio
import random
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BaseScraper(ABC):
    def __init__(self, name: str):
        self.name = name
        self.driver = None
    
    def setup_chrome_driver(self, headless: bool = True):
        from config import Config
        options = Config.get_chrome_options()
        return webdriver.Chrome(options=options)
    
    @abstractmethod
    async def scrape_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        pass
    
    async def random_delay(self, min_s: float = 1.0, max_s: float = 3.0):
        await asyncio.sleep(random.uniform(min_s, max_s))
    
    def cleanup(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
'''
        with open(base_file, 'w', encoding='utf-8') as f:
            f.write(base_content)
    
    # Créer wttj_scraper.py si manquant
    wttj_file = os.path.join(scrapers_dir, 'wttj_scraper.py')
    if not os.path.exists(wttj_file):
        wttj_content = '''# scrapers/wttj_scraper.py
import asyncio
import time
import logging
from typing import List, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from scrapers.base_scraper import BaseScraper
import urllib.parse

logger = logging.getLogger(__name__)

class WTTJScraper(BaseScraper):
    def __init__(self):
        super().__init__('WTTJ')
        self.base_url = 'https://www.welcometothejungle.com'
    
    async def scrape_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        jobs = []
        
        try:
            logger.info(f"🚀 Démarrage scraping RÉEL WTTJ (limite: {limit})")
            self.driver = self.setup_chrome_driver()
            
            search_terms = ['développeur', 'data']
            
            for term in search_terms[:1]:  # Limiter pour les tests
                if len(jobs) >= limit:
                    break
                
                logger.info(f"🔍 Recherche WTTJ: '{term}'")
                term_jobs = await self.scrape_search_term(term, limit - len(jobs))
                jobs.extend(term_jobs)
                
                await self.random_delay(3, 5)
            
            logger.info(f"✅ WTTJ: {len(jobs)} offres trouvées")
            return jobs
            
        except Exception as e:
            logger.error(f"❌ Erreur WTTJ: {e}")
            return []
        finally:
            self.cleanup()
    
    async def scrape_search_term(self, term: str, max_jobs: int) -> List[Dict[str, Any]]:
        jobs = []
        
        try:
            search_url = f"{self.base_url}/fr/jobs?query={urllib.parse.quote(term)}&refinementList%5Boffices.country_code%5D%5B0%5D=FR"
            
            logger.info(f"🌐 Navigation: {search_url}")
            self.driver.get(search_url)
            await self.random_delay(3, 5)
            
            # Gérer cookies
            await self.handle_cookies()
            
            # Attendre résultats
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='jobs-search-item'], .ais-Hits-item, .sc-job-card"))
                )
            except TimeoutException:
                logger.warning("⚠️ Pas de résultats WTTJ")
                return jobs
            
            # Extraction des cartes
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='jobs-search-item'], .ais-Hits-item, .sc-job-card")
            logger.info(f"📋 {len(job_cards)} cartes trouvées")
            
            for i, card in enumerate(job_cards[:max_jobs]):
                try:
                    job_data = await self.extract_job_from_card(card, i)
                    if job_data:
                        jobs.append(job_data)
                    
                    await self.random_delay(1, 2)
                    
                except Exception as e:
                    logger.debug(f"Erreur carte {i}: {e}")
                    continue
            
            return jobs
            
        except Exception as e:
            logger.error(f"❌ Erreur terme '{term}': {e}")
            return jobs
    
    async def extract_job_from_card(self, job_card, index: int):
        try:
            # Titre
            title_elem = None
            title_selectors = [
                "[data-testid='job-card-title']",
                ".wui-text--medium",
                "h3", "h4",
                ".sc-job-title",
                "a[href*='/jobs/']"
            ]
            
            for selector in title_selectors:
                try:
                    title_elem = job_card.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            title = title_elem.text.strip() if title_elem else ""
            
            # Entreprise
            company_elem = None
            company_selectors = [
                "[data-testid='job-card-organization-name']",
                ".wui-text--small",
                ".sc-company-name"
            ]
            
            for selector in company_selectors:
                try:
                    company_elem = job_card.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            company = company_elem.text.strip() if company_elem else ""
            
            # Localisation
            location_elem = None
            location_selectors = [
                "[data-testid='job-card-location']",
                ".sc-location"
            ]
            
            for selector in location_selectors:
                try:
                    location_elem = job_card.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            location = location_elem.text.strip() if location_elem else ""
            
            # URL
            job_url = ""
            try:
                link_elem = job_card.find_element(By.CSS_SELECTOR, "a[href*='/jobs/']")
                job_url = link_elem.get_attribute('href')
            except NoSuchElementException:
                pass
            
            if title and company:
                job_data = {
                    'title': title,
                    'company': company,
                    'location': location,
                    'description': f"Offre {title} chez {company}",
                    'url': job_url,
                    'source': 'wttj',
                    'scraped_at': time.time(),
                    'scraper_type': 'REAL_SELENIUM'
                }
                
                logger.info(f"✅ Offre extraite: {title} - {company}")
                return job_data
            
            return None
            
        except Exception as e:
            logger.debug(f"Erreur extraction carte {index}: {e}")
            return None
    
    async def handle_cookies(self):
        try:
            cookie_selectors = [
                "#onetrust-accept-btn-handler",
                "[data-testid='cookie-accept-button']",
                ".wui-button--primary",
                "button[id*='accept']"
            ]
            
            for selector in cookie_selectors:
                try:
                    accept_btn = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    accept_btn.click()
                    await self.random_delay(1, 2)
                    logger.debug("✅ Cookies acceptés")
                    return
                except TimeoutException:
                    continue
        except Exception as e:
            logger.debug(f"Gestion cookies: {e}")
'''
        with open(wttj_file, 'w', encoding='utf-8') as f:
            f.write(wttj_content)
    
    # Créer indeed_scraper.py si manquant
    indeed_file = os.path.join(scrapers_dir, 'indeed_scraper.py')
    if not os.path.exists(indeed_file):
        indeed_content = '''# scrapers/indeed_scraper.py
import asyncio
import time
import logging
from typing import List, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from scrapers.base_scraper import BaseScraper
import urllib.parse

logger = logging.getLogger(__name__)

class IndeedScraper(BaseScraper):
    def __init__(self):
        super().__init__('Indeed')
        self.base_url = 'https://fr.indeed.com'
    
    async def scrape_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        jobs = []
        
        try:
            logger.info(f"🚀 Démarrage scraping RÉEL Indeed (limite: {limit})")
            self.driver = self.setup_chrome_driver()
            
            search_terms = ['développeur python']
            
            for term in search_terms[:1]:
                if len(jobs) >= limit:
                    break
                
                logger.info(f"🔍 Recherche Indeed: '{term}'")
                term_jobs = await self.scrape_search_term(term, limit - len(jobs))
                jobs.extend(term_jobs)
                
                await self.random_delay(4, 6)
            
            logger.info(f"✅ Indeed: {len(jobs)} offres trouvées")
            return jobs
            
        except Exception as e:
            logger.error(f"❌ Erreur Indeed: {e}")
            return []
        finally:
            self.cleanup()
    
    async def scrape_search_term(self, term: str, max_jobs: int) -> List[Dict[str, Any]]:
        jobs = []
        
        try:
            params = {
                'q': term,
                'l': 'France',
                'sort': 'date'
            }
            search_url = f"{self.base_url}/jobs?" + urllib.parse.urlencode(params)
            
            logger.info(f"🌐 Navigation: {search_url}")
            self.driver.get(search_url)
            await self.random_delay(3, 5)
            
            # Gérer cookies
            await self.handle_cookies()
            
            # Attendre résultats
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-jk], .job_seen_beacon, .slider_container .slider_item"))
                )
            except TimeoutException:
                logger.warning("⚠️ Pas de résultats Indeed")
                return jobs
            
            # Extraction
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, "[data-jk], .job_seen_beacon, .slider_container .slider_item")
            logger.info(f"📋 {len(job_cards)} cartes Indeed trouvées")
            
            for i, card in enumerate(job_cards[:max_jobs]):
                try:
                    job_data = await self.extract_job_from_card(card, i)
                    if job_data:
                        jobs.append(job_data)
                    
                    await self.random_delay(1, 2)
                    
                except Exception as e:
                    logger.debug(f"Erreur carte Indeed {i}: {e}")
                    continue
            
            return jobs
            
        except Exception as e:
            logger.error(f"❌ Erreur terme Indeed '{term}': {e}")
            return jobs
    
    async def extract_job_from_card(self, job_card, index: int):
        try:
            # Titre
            title_elem = None
            title_selectors = [
                "[data-testid='job-title'] a",
                ".jobTitle a",
                "h2 a"
            ]
            
            for selector in title_selectors:
                try:
                    title_elem = job_card.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            title = title_elem.text.strip() if title_elem else ""
            
            # URL
            job_url = title_elem.get_attribute('href') if title_elem else ""
            if job_url and not job_url.startswith('http'):
                job_url = self.base_url + job_url
            
            # Entreprise
            company_elem = None
            company_selectors = [
                "[data-testid='company-name']",
                ".companyName"
            ]
            
            for selector in company_selectors:
                try:
                    company_elem = job_card.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            company = company_elem.text.strip() if company_elem else ""
            
            # Localisation
            location_elem = None
            location_selectors = [
                "[data-testid='job-location']",
                ".companyLocation"
            ]
            
            for selector in location_selectors:
                try:
                    location_elem = job_card.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            location = location_elem.text.strip() if location_elem else ""
            
            if title and company:
                job_data = {
                    'title': title,
                    'company': company,
                    'location': location,
                    'description': f"Offre {title} chez {company}",
                    'url': job_url,
                    'source': 'indeed',
                    'scraped_at': time.time(),
                    'scraper_type': 'REAL_SELENIUM'
                }
                
                logger.info(f"✅ Offre Indeed extraite: {title} - {company}")
                return job_data
            
            return None
            
        except Exception as e:
            logger.debug(f"Erreur extraction Indeed {index}: {e}")
            return None
    
    async def handle_cookies(self):
        try:
            accept_btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#onetrust-accept-btn-handler, .gdpr-button-accept"))
            )
            accept_btn.click()
            await self.random_delay(1, 2)
            logger.debug("✅ Cookies Indeed acceptés")
        except TimeoutException:
            pass
        except Exception as e:
            logger.debug(f"Gestion cookies Indeed: {e}")
'''
        with open(indeed_file, 'w', encoding='utf-8') as f:
            f.write(indeed_content)

# S'assurer que les scrapers existent avant import
ensure_scrapers_exist()

# Import des scrapers RÉELS
try:
    from scrapers.wttj_scraper import WTTJScraper
    WTTJ_AVAILABLE = True
except ImportError as e:
    WTTJ_AVAILABLE = False
    logging.error(f"❌ WTTJ Scraper non disponible: {e}")

try:
    from scrapers.indeed_scraper import IndeedScraper
    INDEED_AVAILABLE = True
except ImportError as e:
    INDEED_AVAILABLE = False
    logging.error(f"❌ Indeed Scraper non disponible: {e}")

try:
    from scrapers.linkedin_scraper import LinkedInScraper
    LINKEDIN_AVAILABLE = True
except ImportError as e:
    LINKEDIN_AVAILABLE = False
    logging.error(f"❌ LinkedIn Scraper non disponible: {e}")

from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScrapingOrchestrator:
    """Orchestrateur principal pour le scraping RÉEL multi-sites"""
    
    def __init__(self):
        self.scrapers = {}
        self.linkedin_credentials = {
            'email': Config.LINKEDIN_EMAIL,
            'password': Config.LINKEDIN_PASSWORD
        }
        
        # Initialisation STRICTE des scrapers réels uniquement
        self._initialize_real_scrapers()
        
        # Initialisation de la base de connaissances
        try:
            from models.knowledge_base import KnowledgeBase
            self.knowledge_base = KnowledgeBase()
            logger.info("✅ Base de connaissances initialisée")
        except Exception as e:
            logger.error(f"❌ Erreur initialisation base de connaissances: {e}")
            self.knowledge_base = None
        
        self.last_scrape = None
        self.scraping_stats = {
            'total_jobs': 0,
            'last_update': None,
            'errors': [],
            'sources_stats': {},
            'duration_seconds': 0,
            'mode': 'REAL_ONLY'
        }
    
    def _initialize_real_scrapers(self):
        """Initialise UNIQUEMENT les scrapers réels disponibles"""
        
        scrapers_initialized = 0
        
        # WTTJ Scraper réel
        if WTTJ_AVAILABLE:
            try:
                self.scrapers['wttj'] = WTTJScraper()
                logger.info("✅ Scraper WTTJ RÉEL initialisé")
                scrapers_initialized += 1
            except Exception as e:
                logger.error(f"❌ Erreur initialisation WTTJ réel: {e}")
        else:
            logger.warning("⚠️ Scraper WTTJ réel non disponible")
        
        # Indeed Scraper réel
        if INDEED_AVAILABLE:
            try:
                self.scrapers['indeed'] = IndeedScraper()
                logger.info("✅ Scraper Indeed RÉEL initialisé")
                scrapers_initialized += 1
            except Exception as e:
                logger.error(f"❌ Erreur initialisation Indeed réel: {e}")
        else:
            logger.warning("⚠️ Scraper Indeed réel non disponible")
        
        # LinkedIn Scraper réel - UNIQUEMENT si credentials configurés
        if self.linkedin_credentials['email'] and self.linkedin_credentials['password']:
            if LINKEDIN_AVAILABLE:
                try:
                    self.scrapers['linkedin'] = LinkedInScraper()
                    logger.info("✅ Scraper LinkedIn RÉEL initialisé")
                    scrapers_initialized += 1
                except Exception as e:
                    logger.error(f"❌ Erreur initialisation LinkedIn réel: {e}")
            else:
                logger.warning("⚠️ Scraper LinkedIn réel non disponible")
        else:
            logger.info("ℹ️ LinkedIn non configuré (ajoutez LINKEDIN_EMAIL et LINKEDIN_PASSWORD dans .env)")
        
        if scrapers_initialized == 0:
            logger.warning("⚠️ AUCUN scraper réel initialisé ! Les scrapers vont être créés automatiquement")
        
        logger.info(f"🎯 {scrapers_initialized} scraper(s) réel(s) initialisé(s): {list(self.scrapers.keys())}")
    
    def get_available_real_sources(self) -> List[str]:
        """Retourne uniquement les sources réelles disponibles"""
        available = list(self.scrapers.keys())
        logger.info(f"📋 Sources RÉELLES disponibles: {available}")
        return available
    
    async def run_full_scrape(self, sources: List[str] = None, max_jobs: int = None) -> Dict[str, Any]:
        """Lance un scraping complet RÉEL uniquement"""
        
        # Vérification des sources réelles disponibles
        available_sources = self.get_available_real_sources()
        
        if not available_sources:
            error_msg = "Aucun scraper réel disponible. Les fichiers scrapers/ ont été créés automatiquement."
            logger.warning(f"⚠️ {error_msg}")
            
            # Réessayer l'initialisation après création automatique
            self._initialize_real_scrapers()
            available_sources = self.get_available_real_sources()
            
            if not available_sources:
                return {
                    'total_jobs': 0,
                    'sources_stats': {},
                    'errors': [error_msg],
                    'duration_seconds': 0,
                    'mode': 'REAL_ONLY',
                    'status': 'NO_SCRAPERS'
                }
        
        # Sélection des sources à scraper
        if sources is None:
            sources = available_sources
            logger.info(f"🎯 Auto-sélection de toutes les sources réelles: {sources}")
        else:
            # Filtrer pour garder uniquement les sources réelles disponibles
            valid_sources = [s for s in sources if s in available_sources]
            if not valid_sources:
                error_msg = f"Aucune source réelle disponible parmi {sources}. Disponibles: {available_sources}"
                logger.error(f"❌ {error_msg}")
                return {
                    'total_jobs': 0,
                    'sources_stats': {},
                    'errors': [error_msg],
                    'duration_seconds': 0,
                    'mode': 'REAL_ONLY',
                    'status': 'INVALID_SOURCES'
                }
            sources = valid_sources
        
        if max_jobs is None:
            max_jobs = Config.MAX_JOBS_PER_SCRAPE
        
        logger.info(f"🚀 Début du scraping RÉEL pour : {sources}")
        logger.info(f"🎯 Objectif: {max_jobs} offres maximum")
        logger.info(f"🔧 Mode navigateur: {'VISIBLE' if not Config.SELENIUM_HEADLESS else 'HEADLESS'}")
        
        start_time = datetime.now()
        all_jobs = []
        source_results = {}
        
        # Répartition équitable du nombre de jobs par source
        jobs_per_source = max(1, max_jobs // len(sources))
        
        for source in sources:
            try:
                logger.info(f"📡 Scraping RÉEL {source.upper()}...")
                scraper = self.scrapers[source]
                
                # Gestion spéciale pour LinkedIn RÉEL
                if source == 'linkedin':
                    if not self.linkedin_credentials['email']:
                        error_msg = "Credentials LinkedIn manquants pour le scraping réel"
                        logger.error(f"❌ {error_msg}")
                        source_results[source] = {
                            'jobs_count': 0,
                            'status': 'credentials_missing',
                            'error': error_msg,
                            'scraper_type': 'REAL'
                        }
                        continue
                    
                    # Connexion LinkedIn RÉELLE
                    try:
                        if hasattr(scraper, 'login_linkedin'):
                            login_success = await scraper.login_linkedin(
                                self.linkedin_credentials['email'],
                                self.linkedin_credentials['password']
                            )
                            
                            if not login_success:
                                error_msg = "Échec de connexion LinkedIn réelle"
                                logger.error(f"❌ {error_msg}")
                                source_results[source] = {
                                    'jobs_count': 0,
                                    'status': 'login_failed',
                                    'error': error_msg,
                                    'scraper_type': 'REAL'
                                }
                                continue
                    except Exception as e:
                        error_msg = f"Erreur connexion LinkedIn réelle: {str(e)}"
                        logger.error(f"❌ {error_msg}")
                        source_results[source] = {
                            'jobs_count': 0,
                            'status': 'login_error',
                            'error': error_msg,
                            'scraper_type': 'REAL'
                        }
                        continue
                
                # Lancement du scraping RÉEL
                logger.info(f"🕷️ Démarrage scraping RÉEL {source} (limite: {jobs_per_source})")
                logger.info(f"👀 {'Navigateur VISIBLE' if not Config.SELENIUM_HEADLESS else 'Mode headless'}")
                
                jobs = await scraper.scrape_jobs(limit=jobs_per_source)
                
                logger.info(f"✅ {len(jobs)} offres RÉELLES récupérées de {source.upper()}")
                all_jobs.extend(jobs)
                
                source_results[source] = {
                    'jobs_count': len(jobs),
                    'status': 'success',
                    'sample_titles': [job.get('title', 'Sans titre') for job in jobs[:3]],
                    'scraper_type': 'REAL',
                    'real_data': True
                }
                
                # Délai respectueux entre sources
                if source != sources[-1]:  # Pas de délai après la dernière source
                    delay = Config.REQUEST_DELAY * 2
                    logger.info(f"⏳ Délai anti-détection {delay}s avant source suivante...")
                    await asyncio.sleep(delay)
                
            except Exception as e:
                error_msg = f"Erreur scraping RÉEL {source}: {str(e)}"
                logger.error(f"❌ {error_msg}")
                
                source_results[source] = {
                    'jobs_count': 0,
                    'status': 'error',
                    'error': error_msg,
                    'scraper_type': 'REAL'
                }
                
                self.scraping_stats['errors'].append({
                    'source': source,
                    'error': error_msg,
                    'timestamp': datetime.now().isoformat(),
                    'type': 'REAL_SCRAPING_ERROR'
                })
        
        # Traitement des offres RÉELLES collectées
        processed_jobs = []
        if all_jobs:
            logger.info(f"🔄 Traitement de {len(all_jobs)} offres RÉELLES...")
            processed_jobs = await self.process_real_jobs(all_jobs)
            
            if self.knowledge_base:
                await self.store_jobs(processed_jobs)
        
        # Mise à jour des statistiques
        duration = (datetime.now() - start_time).total_seconds()
        successful_sources = [k for k, v in source_results.items() if v['status'] == 'success']
        
        self.scraping_stats.update({
            'total_jobs': len(processed_jobs),
            'last_update': datetime.now().isoformat(),
            'duration_seconds': duration,
            'sources_stats': source_results,
            'sources_requested': sources,
            'sources_successful': successful_sources,
            'mode': 'REAL_ONLY',
            'status': 'SUCCESS' if processed_jobs else 'NO_DATA'
        })
        
        self.last_scrape = datetime.now()
        
        logger.info(f"🎉 Scraping RÉEL terminé : {len(processed_jobs)} offres en {duration:.1f}s")
        
        # Sauvegarde du rapport RÉEL
        await self.save_real_scraping_report(all_jobs, processed_jobs, source_results)
        
        return self.scraping_stats
    
    async def process_real_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Traite et enrichit les offres RÉELLES collectées"""
        logger.info(f"🔄 Traitement avancé de {len(jobs)} offres RÉELLES...")
        
        processed = []
        duplicates_removed = 0
        seen_jobs = set()
        
        for job in jobs:
            try:
                # Nettoyage et normalisation
                clean_job = {
                    'title': self.clean_text(job.get('title', '')),
                    'company': self.clean_text(job.get('company', '')),
                    'location': self.clean_text(job.get('location', '')),
                    'description': self.clean_text(job.get('description', '')),
                    'url': job.get('url', ''),
                    'source': job.get('source', 'unknown'),
                    'scraped_at': datetime.now().isoformat(),
                    'data_type': 'REAL',
                    'scraper_type': job.get('scraper_type', 'REAL_SELENIUM')
                }
                
                # Déduplication stricte
                job_signature = f"{clean_job['title'].lower()}_{clean_job['company'].lower()}"
                if job_signature in seen_jobs:
                    duplicates_removed += 1
                    continue
                seen_jobs.add(job_signature)
                
                # Copie des données enrichies du scraping réel
                enriched_fields = [
                    'technologies', 'experience_level', 'remote', 'contract_type', 
                    'salary', 'benefits', 'company_info', 'full_description'
                ]
                
                for field in enriched_fields:
                    if field in job:
                        clean_job[field] = job[field]
                
                # Génération d'un hash unique
                clean_job['hash_id'] = self.generate_job_hash(clean_job)
                
                processed.append(clean_job)
                
            except Exception as e:
                logger.error(f"Erreur traitement offre RÉELLE: {e}")
                continue
        
        logger.info(f"✅ {len(processed)} offres RÉELLES traitées ({duplicates_removed} doublons supprimés)")
        return processed
    
    def clean_text(self, text: str) -> str:
        """Nettoyage avancé du texte pour données réelles"""
        import re
        if not text:
            return ""
        
        # Suppression HTML et caractères spéciaux
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\-\.,;:!?()\[\]\'\"€]', ' ', text)
        text = text.strip()
        
        return text[:10000]  # Limite généreuse pour données réelles
    
    def generate_job_hash(self, job: Dict[str, Any]) -> str:
        """Génère un hash unique pour l'offre réelle"""
        import hashlib
        
        unique_string = f"{job.get('title', '')}{job.get('company', '')}{job.get('source', '')}REAL"
        return hashlib.md5(unique_string.encode()).hexdigest()
    
    async def store_jobs(self, jobs: List[Dict]) -> None:
        """Stockage des offres RÉELLES dans la base de connaissances"""
        if not self.knowledge_base:
            logger.warning("⚠️ Base de connaissances non disponible pour stockage")
            return
            
        logger.info(f"💾 Stockage de {len(jobs)} offres RÉELLES...")
        
        stored_count = 0
        for job in jobs:
            try:
                success = await self.knowledge_base.store_job(job)
                if success:
                    stored_count += 1
            except Exception as e:
                logger.error(f"Erreur stockage offre RÉELLE {job.get('title', 'Unknown')}: {e}")
        
        logger.info(f"✅ {stored_count} nouvelles offres RÉELLES stockées")
    
    async def save_real_scraping_report(self, raw_jobs: List[Dict], 
                                       processed_jobs: List[Dict], 
                                       source_results: Dict[str, Any]) -> None:
        """Sauvegarde un rapport détaillé du scraping RÉEL"""
        try:
            os.makedirs(Config.REPORTS_DIR, exist_ok=True)
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'mode': 'REAL_SCRAPING_ONLY',
                'summary': {
                    'raw_jobs_collected': len(raw_jobs),
                    'processed_jobs': len(processed_jobs),
                    'sources_attempted': list(source_results.keys()),
                    'successful_sources': [k for k, v in source_results.items() if v['status'] == 'success'],
                    'total_duration': self.scraping_stats.get('duration_seconds', 0),
                    'data_quality': 'REAL_DATA_ONLY',
                    'browser_mode': 'VISIBLE' if not Config.SELENIUM_HEADLESS else 'HEADLESS'
                },
                'source_details': source_results,
                'configuration': {
                    'linkedin_configured': bool(self.linkedin_credentials['email']),
                    'available_real_scrapers': list(self.scrapers.keys()),
                    'demo_mode': False,
                    'real_mode_only': True,
                    'selenium_headless': Config.SELENIUM_HEADLESS,
                    'request_delay': Config.REQUEST_DELAY
                },
                'sample_real_jobs': processed_jobs[:3] if processed_jobs else []
            }
            
            filename = f"{Config.REPORTS_DIR}/REAL_scraping_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📊 Rapport de scraping RÉEL sauvegardé: {filename}")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde rapport RÉEL: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du scraping RÉEL"""
        base_stats = {
            **self.scraping_stats,
            'available_real_scrapers': list(self.scrapers.keys()),
            'linkedin_configured': bool(self.linkedin_credentials['email']),
            'last_scrape_time': self.last_scrape.isoformat() if self.last_scrape else None,
            'mode': 'REAL_ONLY',
            'demo_scrapers': [],  # Aucun scraper démo
            'total_real_scrapers': len(self.scrapers),
            'browser_mode': 'VISIBLE' if not Config.SELENIUM_HEADLESS else 'HEADLESS',
            'selenium_config': {
                'headless': Config.SELENIUM_HEADLESS,
                'request_delay': Config.REQUEST_DELAY,
                'timeout': Config.SELENIUM_TIMEOUT
            }
        }
        
        # Stats de la base de connaissances
        if self.knowledge_base:
            try:
                kb_stats = self.knowledge_base.get_stats()
                base_stats['knowledge_base_stats'] = kb_stats
            except Exception as e:
                base_stats['knowledge_base_error'] = str(e)
        
        return base_stats
    
    async def test_real_scrapers(self) -> Dict[str, Any]:
        """Test de connectivité des scrapers RÉELS uniquement"""
        results = {}
        
        if not self.scrapers:
            return {
                'error': 'Aucun scraper réel disponible',
                'available_scrapers': 0,
                'message': 'Les scrapers ont été créés automatiquement, relancez le test'
            }
        
        for name, scraper in self.scrapers.items():
            try:
                logger.info(f"🧪 Test du scraper RÉEL {name.upper()}...")
                
                if name == 'linkedin' and not self.linkedin_credentials['email']:
                    results[name] = {
                        'status': 'credentials_required',
                        'message': 'Credentials LinkedIn requis pour le test',
                        'scraper_type': 'REAL'
                    }
                    continue
                
                # Test avec 1 seule offre réelle
                test_jobs = await scraper.scrape_jobs(limit=1)
                
                results[name] = {
                    'status': 'success' if test_jobs else 'no_results',
                    'jobs_found': len(test_jobs),
                    'sample_job': test_jobs[0] if test_jobs else None,
                    'scraper_type': 'REAL',
                    'data_quality': 'REAL_DATA'
                }
                
            except Exception as e:
                results[name] = {
                    'status': 'error',
                    'error': str(e),
                    'scraper_type': 'REAL'
                }
        
        return {
            'mode': 'REAL_TESTING_ONLY',
            'scrapers_tested': len(results),
            'results': results,
            'browser_mode': 'VISIBLE' if not Config.SELENIUM_HEADLESS else 'HEADLESS'
        }
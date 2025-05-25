# create_real_scrapers.py - Créer les vrais scrapers Selenium
"""
Script pour créer les scrapers Selenium réels pour LinkedBoost
AUCUN mode démo - uniquement du scraping réel
"""

import os

def create_scrapers_directory():
    """Crée le répertoire scrapers"""
    os.makedirs('scrapers', exist_ok=True)
    print("✅ Répertoire scrapers/ créé")

def create_scrapers_init():
    """Crée __init__.py pour le package scrapers"""
    init_content = '''# scrapers/__init__.py
"""
Package de scrapers RÉELS pour LinkedBoost
Aucun mode démo - uniquement du scraping Selenium réel
"""

__version__ = "1.0.0"
__all__ = []

# Import des scrapers réels disponibles
try:
    from .wttj_scraper import WTTJScraper
    __all__.append('WTTJScraper')
except ImportError:
    pass

try:
    from .linkedin_scraper import LinkedInScraper
    __all__.append('LinkedInScraper')
except ImportError:
    pass

try:
    from .indeed_scraper import IndeedScraper
    __all__.append('IndeedScraper')
except ImportError:
    pass
'''
    
    with open('scrapers/__init__.py', 'w', encoding='utf-8') as f:
        f.write(init_content)
    print("✅ scrapers/__init__.py créé")

def create_base_scraper():
    """Crée la classe de base pour les scrapers Selenium"""
    base_content = '''# scrapers/base_scraper.py - Classe de base pour scrapers Selenium RÉELS
import asyncio
import random
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Classe de base pour tous les scrapers Selenium RÉELS"""
    
    def __init__(self, name: str):
        self.name = name
        self.driver = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    def setup_chrome_driver(self, headless: bool = True) -> webdriver.Chrome:
        """Configure le driver Chrome pour le scraping réel"""
        options = Options()
        
        # Configuration anti-détection
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # User agent réaliste
        options.add_argument(f'--user-agent={self.headers["User-Agent"]}')
        
        # Fenêtre réaliste
        options.add_argument('--window-size=1920,1080')
        
        # Mode headless si demandé
        if headless:
            options.add_argument('--headless')
        
        # Optimisations performances
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        
        # Langue française
        options.add_argument('--lang=fr-FR')
        options.add_experimental_option('prefs', {'intl.accept_languages': 'fr-FR,fr'})
        
        try:
            driver = webdriver.Chrome(options=options)
            
            # Masquer les signes d'automation
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Timeouts
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            
            return driver
            
        except Exception as e:
            logger.error(f"❌ Erreur création driver Chrome: {e}")
            raise
    
    @abstractmethod
    async def scrape_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Méthode principale de scraping à implémenter"""
        pass
    
    async def random_delay(self, min_seconds: float = 2.0, max_seconds: float = 5.0):
        """Délai aléatoire pour simuler un comportement humain"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    async def human_type(self, element, text: str):
        """Simulation de frappe humaine"""
        for char in text:
            element.send_keys(char)
            await asyncio.sleep(random.uniform(0.05, 0.15))
    
    def wait_for_element(self, by: By, value: str, timeout: int = 10):
        """Attendre qu'un élément soit présent"""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
    
    def safe_find_element(self, by: By, value: str):
        """Recherche sécurisée d'élément"""
        try:
            return self.driver.find_element(by, value)
        except NoSuchElementException:
            return None
    
    def safe_find_elements(self, by: By, value: str):
        """Recherche sécurisée d'éléments multiples"""
        try:
            return self.driver.find_elements(by, value)
        except NoSuchElementException:
            return []
    
    def cleanup(self):
        """Nettoyage du driver"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
    
    def __del__(self):
        """Destructeur pour nettoyer le driver"""
        self.cleanup()
'''
    
    with open('scrapers/base_scraper.py', 'w', encoding='utf-8') as f:
        f.write(base_content)
    print("✅ scrapers/base_scraper.py créé")

def create_wttj_real_scraper():
    """Crée le scraper WTTJ réel avec Selenium"""
    wttj_content = '''# scrapers/wttj_scraper.py - Scraper WTTJ RÉEL avec Selenium
import asyncio
import time
import logging
from typing import List, Dict, Any, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from scrapers.base_scraper import BaseScraper
import urllib.parse

logger = logging.getLogger(__name__)

class WTTJScraper(BaseScraper):
    """Scraper RÉEL Welcome to the Jungle avec Selenium"""
    
    def __init__(self):
        super().__init__('Welcome to the Jungle')
        self.base_url = 'https://www.welcometothejungle.com'
        self.search_url = f"{self.base_url}/fr/jobs"
    
    async def scrape_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Scraping RÉEL des offres WTTJ"""
        jobs = []
        
        try:
            logger.info(f"🚀 Démarrage scraping RÉEL WTTJ (limite: {limit})")
            
            # Configuration du driver
            self.driver = self.setup_chrome_driver(headless=True)
            
            search_terms = ['développeur', 'data', 'marketing', 'commercial']
            
            for term in search_terms:
                if len(jobs) >= limit:
                    break
                
                logger.info(f"🔍 Recherche RÉELLE WTTJ: '{term}'")
                term_jobs = await self.scrape_search_term(term, limit - len(jobs))
                jobs.extend(term_jobs)
                
                # Délai entre recherches
                await self.random_delay(3, 7)
            
            logger.info(f"✅ WTTJ RÉEL: {len(jobs)} offres collectées")
            return jobs[:limit]
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping RÉEL WTTJ: {e}")
            return []
        finally:
            self.cleanup()
    
    async def scrape_search_term(self, term: str, max_jobs: int) -> List[Dict[str, Any]]:
        """Scraping pour un terme de recherche spécifique"""
        jobs = []
        
        try:
            # Construction URL de recherche
            search_url = f"{self.search_url}?query={urllib.parse.quote(term)}&refinementList%5Boffices.country_code%5D%5B0%5D=FR"
            
            logger.info(f"🌐 Navigation vers: {search_url}")
            self.driver.get(search_url)
            await self.random_delay(3, 5)
            
            # Gérer les cookies
            await self.handle_cookies()
            
            # Attendre le chargement des résultats
            try:
                self.wait_for_element(By.CSS_SELECTOR, "[data-testid='jobs-search-item'], .ais-Hits-item", 15)
            except TimeoutException:
                logger.warning("⚠️ Timeout attente résultats WTTJ")
                return jobs
            
            # Scroll pour charger plus de résultats
            await self.scroll_and_load_jobs(max_jobs)
            
            # Extraction des offres
            job_cards = self.safe_find_elements(By.CSS_SELECTOR, "[data-testid='jobs-search-item'], .ais-Hits-item")
            logger.info(f"📋 {len(job_cards)} cartes d'offres trouvées")
            
            for i, card in enumerate(job_cards[:max_jobs]):
                try:
                    job_data = await self.extract_job_from_card(card, i)
                    if job_data:
                        jobs.append(job_data)
                    
                    await self.random_delay(1, 3)
                    
                except Exception as e:
                    logger.debug(f"Erreur extraction carte {i}: {e}")
                    continue
            
            return jobs
            
        except Exception as e:
            logger.error(f"❌ Erreur terme '{term}': {e}")
            return jobs
    
    async def extract_job_from_card(self, job_card, index: int) -> Optional[Dict[str, Any]]:
        """Extraction RÉELLE des données d'une carte d'offre"""
        try:
            # Titre du poste
            title_elem = job_card.find_element(By.CSS_SELECTOR, "[data-testid='job-card-title'], .wui-text--medium, h3, h4")
            title = title_elem.text.strip() if title_elem else ""
            
            # Entreprise
            company_elem = job_card.find_element(By.CSS_SELECTOR, "[data-testid='job-card-organization-name'], .wui-text--small")
            company = company_elem.text.strip() if company_elem else ""
            
            # Localisation
            location_elem = job_card.find_element(By.CSS_SELECTOR, "[data-testid='job-card-location'], .sc-location")
            location = location_elem.text.strip() if location_elem else ""
            
            # URL de l'offre
            link_elem = job_card.find_element(By.CSS_SELECTOR, "a[href*='/jobs/']")
            job_url = link_elem.get_attribute('href') if link_elem else ""
            
            # Description courte
            desc_elem = job_card.find_element(By.CSS_SELECTOR, ".wui-text--caption, [data-testid='job-card-excerpt']")
            description = desc_elem.text.strip() if desc_elem else ""
            
            # Tags/Technologies
            tag_elements = job_card.find_elements(By.CSS_SELECTOR, ".wui-tag, [data-testid='job-card-tag']")
            technologies = [tag.text.strip() for tag in tag_elements if tag.text.strip()]
            
            # Type de contrat
            contract_elem = job_card.find_element(By.CSS_SELECTOR, "[data-testid='job-card-contract-type']")
            contract_type = contract_elem.text.strip() if contract_elem else "CDI"
            
            if title and company:
                job_data = {
                    'title': title,
                    'company': company,
                    'location': location,
                    'description': description,
                    'technologies': technologies,
                    'contract_type': contract_type,
                    'url': job_url,
                    'source': 'wttj',
                    'scraped_at': time.time(),
                    'scraper_type': 'REAL_SELENIUM'
                }
                
                logger.debug(f"✅ Offre extraite: {title} - {company}")
                return job_data
            
            return None
            
        except NoSuchElementException as e:
            logger.debug(f"Élément manquant carte {index}: {e}")
            return None
        except Exception as e:
            logger.debug(f"Erreur extraction carte {index}: {e}")
            return None
    
    async def handle_cookies(self):
        """Gestion des cookies WTTJ"""
        try:
            accept_selectors = [
                "#onetrust-accept-btn-handler",
                "[data-testid='cookie-accept-button']",
                ".wui-button--primary",
                "button[id*='accept']"
            ]
            
            for selector in accept_selectors:
                try:
                    accept_btn = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    accept_btn.click()
                    await self.random_delay(1, 2)
                    logger.debug("✅ Cookies acceptés WTTJ")
                    return
                except TimeoutException:
                    continue
                    
        except Exception as e:
            logger.debug(f"Gestion cookies WTTJ: {e}")
    
    async def scroll_and_load_jobs(self, target_jobs: int):
        """Scroll pour charger plus d'offres"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        for scroll in range(3):  # Limiter les scrolls
            # Scroll vers le bas
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            await self.random_delay(2, 4)
            
            # Nouveau contenu chargé ?
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            current_jobs = len(self.safe_find_elements(By.CSS_SELECTOR, "[data-testid='jobs-search-item'], .ais-Hits-item"))
            
            if current_jobs >= target_jobs or new_height == last_height:
                break
                
            last_height = new_height
            
            # Cliquer sur "Voir plus" si disponible
            try:
                load_more = self.safe_find_element(By.CSS_SELECTOR, "[data-testid='load-more-button']")
                if load_more and load_more.is_displayed():
                    self.driver.execute_script("arguments[0].click();", load_more)
                    await self.random_delay(2, 4)
            except Exception:
                pass
'''
    
    with open('scrapers/wttj_scraper.py', 'w', encoding='utf-8') as f:
        f.write(wttj_content)
    print("✅ scrapers/wttj_scraper.py créé (RÉEL)")

def create_indeed_real_scraper():
    """Crée le scraper Indeed réel avec Selenium"""
    indeed_content = '''# scrapers/indeed_scraper.py - Scraper Indeed RÉEL avec Selenium
import asyncio
import time
import logging
from typing import List, Dict, Any, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from scrapers.base_scraper import BaseScraper
import urllib.parse

logger = logging.getLogger(__name__)

class IndeedScraper(BaseScraper):
    """Scraper RÉEL Indeed avec Selenium"""
    
    def __init__(self):
        super().__init__('Indeed')
        self.base_url = 'https://fr.indeed.com'
        self.search_url = f"{self.base_url}/jobs"
    
    async def scrape_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Scraping RÉEL des offres Indeed"""
        jobs = []
        
        try:
            logger.info(f"🚀 Démarrage scraping RÉEL Indeed (limite: {limit})")
            
            self.driver = self.setup_chrome_driver(headless=True)
            
            search_terms = ['développeur python', 'data scientist', 'chef de projet', 'ingénieur']
            
            for term in search_terms:
                if len(jobs) >= limit:
                    break
                
                logger.info(f"🔍 Recherche RÉELLE Indeed: '{term}'")
                term_jobs = await self.scrape_search_term(term, limit - len(jobs))
                jobs.extend(term_jobs)
                
                await self.random_delay(4, 8)
            
            logger.info(f"✅ Indeed RÉEL: {len(jobs)} offres collectées")
            return jobs[:limit]
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping RÉEL Indeed: {e}")
            return []
        finally:
            self.cleanup()
    
    async def scrape_search_term(self, term: str, max_jobs: int) -> List[Dict[str, Any]]:
        """Scraping Indeed pour un terme spécifique"""
        jobs = []
        
        try:
            # Construction URL
            params = {
                'q': term,
                'l': 'France',
                'sort': 'date',
                'fromage': '7'
            }
            search_url = f"{self.search_url}?" + urllib.parse.urlencode(params)
            
            logger.info(f"🌐 Navigation Indeed: {search_url}")
            self.driver.get(search_url)
            await self.random_delay(3, 6)
            
            # Gérer cookies
            await self.handle_cookies()
            
            # Attendre résultats
            try:
                self.wait_for_element(By.CSS_SELECTOR, "[data-jk], .job_seen_beacon", 15)
            except TimeoutException:
                logger.warning("⚠️ Timeout attente résultats Indeed")
                return jobs
            
            # Extraction offres sur la page
            job_cards = self.safe_find_elements(By.CSS_SELECTOR, "[data-jk], .job_seen_beacon")
            logger.info(f"📋 {len(job_cards)} offres trouvées Indeed")
            
            for i, card in enumerate(job_cards[:max_jobs]):
                try:
                    job_data = await self.extract_job_from_card(card, i)
                    if job_data:
                        jobs.append(job_data)
                    
                    await self.random_delay(1, 2)
                    
                except Exception as e:
                    logger.debug(f"Erreur extraction Indeed {i}: {e}")
                    continue
            
            return jobs
            
        except Exception as e:
            logger.error(f"❌ Erreur terme Indeed '{term}': {e}")
            return jobs
    
    async def extract_job_from_card(self, job_card, index: int) -> Optional[Dict[str, Any]]:
        """Extraction RÉELLE des données Indeed"""
        try:
            # Titre
            title_elem = job_card.find_element(By.CSS_SELECTOR, "[data-testid='job-title'] a, .jobTitle a")
            title = title_elem.text.strip() if title_elem else ""
            
            # URL
            job_url = title_elem.get_attribute('href') if title_elem else ""
            if job_url and not job_url.startswith('http'):
                job_url = self.base_url + job_url
            
            # Entreprise
            company_elem = job_card.find_element(By.CSS_SELECTOR, "[data-testid='company-name'], .companyName")
            company = company_elem.text.strip() if company_elem else ""
            
            # Localisation
            location_elem = job_card.find_element(By.CSS_SELECTOR, "[data-testid='job-location'], .companyLocation")
            location = location_elem.text.strip() if location_elem else ""
            
            # Description
            summary_elem = job_card.find_element(By.CSS_SELECTOR, ".summary, [data-testid='job-snippet']")
            description = summary_elem.text.strip() if summary_elem else ""
            
            # Salaire
            salary = ""
            try:
                salary_elem = job_card.find_element(By.CSS_SELECTOR, ".salary-snippet, [data-testid='job-salary']")
                salary = salary_elem.text.strip()
            except NoSuchElementException:
                pass
            
            # Type contrat
            contract_type = "CDI"
            try:
                contract_elem = job_card.find_element(By.CSS_SELECTOR, ".jobMetadata, .metadata")
                contract_type = contract_elem.text.strip() or "CDI"
            except NoSuchElementException:
                pass
            
            if title and company:
                job_data = {
                    'title': title,
                    'company': company,
                    'location': location,
                    'description': description,
                    'salary': salary,
                    'contract_type': contract_type,
                    'url': job_url,
                    'source': 'indeed',
                    'scraped_at': time.time(),
                    'scraper_type': 'REAL_SELENIUM'
                }
                
                logger.debug(f"✅ Offre Indeed extraite: {title} - {company}")
                return job_data
            
            return None
            
        except Exception as e:
            logger.debug(f"Erreur extraction Indeed {index}: {e}")
            return None
    
    async def handle_cookies(self):
        """Gestion cookies Indeed"""
        try:
            accept_btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#onetrust-accept-btn-handler, .gdpr-button-accept"))
            )
            accept_btn.click()
            await self.random_delay(1, 2)
            logger.debug("✅ Cookies acceptés Indeed")
        except TimeoutException:
            pass
        except Exception as e:
            logger.debug(f"Gestion cookies Indeed: {e}")
'''
    
    with open('scrapers/indeed_scraper.py', 'w', encoding='utf-8') as f:
        f.write(indeed_content)
    print("✅ scrapers/indeed_scraper.py créé (RÉEL)")

def create_linkedin_real_scraper():
    """Crée le scraper LinkedIn réel avec Selenium"""
    linkedin_content = '''# scrapers/linkedin_scraper.py - Scraper LinkedIn RÉEL avec Selenium
import asyncio
import time
import logging
from typing import List, Dict, Any, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class LinkedInScraper(BaseScraper):
    """Scraper RÉEL LinkedIn avec Selenium et authentification"""
    
    def __init__(self):
        super().__init__('LinkedIn')
        self.base_url = 'https://www.linkedin.com'
        self.is_logged_in = False
    
    async def login_linkedin(self, email: str, password: str) -> bool:
        """Connexion RÉELLE à LinkedIn"""
        try:
            logger.info("🔐 Connexion RÉELLE à LinkedIn...")
            
            self.driver = self.setup_chrome_driver(headless=True)
            
            # Page de connexion
            self.driver.get(f'{self.base_url}/login')
            await self.random_delay(2, 4)
            
            # Saisie email
            email_field = self.wait_for_element(By.ID, "username")
            await self.human_type(email_field, email)
            await self.random_delay(1, 2)
            
            # Saisie password
            password_field = self.driver.find_element(By.ID, "password")
            await self.human_type(password_field, password)
            await self.random_delay(1, 2)
            
            # Clic connexion
            login_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_btn.click()
            await self.random_delay(3, 5)
            
            # Vérification connexion
            if self.driver.current_url.startswith(f'{self.base_url}/feed'):
                self.is_logged_in = True
                logger.info("✅ Connexion LinkedIn RÉELLE réussie")
                return True
            
            # Détecter challenges
            if 'challenge' in self.driver.current_url:
                logger.warning("⚠️ Challenge de sécurité LinkedIn détecté")
                return await self.handle_security_challenge()
            
            logger.error("❌ Échec connexion LinkedIn RÉELLE")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur connexion LinkedIn: {e}")
            return False
    
    async def handle_security_challenge(self) -> bool:
        """Gestion des challenges LinkedIn"""
        logger.info("🔍 Traitement challenge sécurité LinkedIn...")
        
        try:
            # Attendre résolution manuelle ou automatique
            WebDriverWait(self.driver, 60).until(
                lambda driver: driver.current_url.startswith(f'{self.base_url}/feed')
            )
            
            self.is_logged_in = True
            logger.info("✅ Challenge LinkedIn résolu")
            return True
            
        except TimeoutException:
            logger.error("❌ Timeout challenge LinkedIn")
            return False
    
    async def scrape_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Scraping RÉEL des offres LinkedIn"""
        if not self.is_logged_in:
            logger.error("❌ Connexion LinkedIn requise pour le scraping")
            return []
        
        jobs = []
        
        try:
            logger.info(f"🚀 Démarrage scraping RÉEL LinkedIn (limite: {limit})")
            
            search_terms = ['développeur python', 'data scientist', 'chef de projet digital']
            
            for term in search_terms:
                if len(jobs) >= limit:
                    break
                
                logger.info(f"🔍 Recherche RÉELLE LinkedIn: '{term}'")
                term_jobs = await self.scrape_search_term(term, limit - len(jobs))
                jobs.extend(term_jobs)
                
                await self.random_delay(5, 10)
            
            logger.info(f"✅ LinkedIn RÉEL: {len(jobs)} offres collectées")
            return jobs[:limit]
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping RÉEL LinkedIn: {e}")
            return []
        finally:
            self.cleanup()
    
    async def scrape_search_term(self, term: str, max_jobs: int) -> List[Dict[str, Any]]:
        """Scraping LinkedIn pour un terme spécifique"""
        jobs = []
        
        try:
            # URL de recherche
            search_url = f"{self.base_url}/jobs/search/?keywords={term.replace(' ', '%20')}&location=France"
            
            logger.info(f"🌐 Navigation LinkedIn: {search_url}")
            self.driver.get(search_url)
            await self.random_delay(3, 5)
            
            # Attendre résultats
            try:
                self.wait_for_element(By.CSS_SELECTOR, ".jobs-search-results", 15)
            except TimeoutException:
                logger.warning("⚠️ Timeout attente résultats LinkedIn")
                return jobs
            
            # Scroll pour charger
            await self.scroll_linkedin_jobs(max_jobs)
            
            # Extraction
            job_cards = self.safe_find_elements(By.CSS_SELECTOR, ".job-card-container, .jobs-search-results__list-item")
            logger.info(f"📋 {len(job_cards)} offres LinkedIn trouvées")
            
            for i, card in enumerate(job_cards[:max_jobs]):
                try:
                    job_data = await self.extract_linkedin_job(card, i)
                    if job_data:
                        jobs.append(job_data)
                    
                    await self.random_delay(2, 4)
                    
                except Exception as e:
                    logger.debug(f"Erreur extraction LinkedIn {i}: {e}")
                    continue
            
            return jobs
            
        except Exception as e:
            logger.error(f"❌ Erreur terme LinkedIn '{term}': {e}")
            return jobs
    
    async def extract_linkedin_job(self, job_card, index: int) -> Optional[Dict[str, Any]]:
        """Extraction RÉELLE job LinkedIn"""
        try:
            # Titre
            title_elem = job_card.find_element(By.CSS_SELECTOR, ".job-card-list__title, .job-card-container__link")
            title = title_elem.text.strip() if title_elem else ""
            
            # Entreprise
            company_elem = job_card.find_element(By.CSS_SELECTOR, ".job-card-container__company-name, .job-card-list__company-name")
            company = company_elem.text.strip() if company_elem else ""
            
            # Localisation
            location_elem = job_card.find_element(By.CSS_SELECTOR, ".job-card-container__metadata-item, .job-card-list__metadata")
            location = location_elem.text.strip() if location_elem else ""
            
            # URL
            link_elem = job_card.find_element(By.CSS_SELECTOR, "a[data-control-name='job_card_click']")
            job_url = link_elem.get_attribute('href') if link_elem else ""
            
            if title and company:
                job_data = {
                    'title': title,
                    'company': company,
                    'location': location,
                    'description': "",  # Nécessiterait clic supplémentaire
                    'url': job_url,
                    'source': 'linkedin',
                    'scraped_at': time.time(),
                    'scraper_type': 'REAL_SELENIUM',
                    'requires_auth': True
                }
                
                logger.debug(f"✅ Offre LinkedIn extraite: {title} - {company}")
                return job_data
            
            return None
            
        except Exception as e:
            logger.debug(f"Erreur extraction LinkedIn {index}: {e}")
            return None
    
    async def scroll_linkedin_jobs(self, target_jobs: int):
        """Scroll LinkedIn pour charger plus d'offres"""
        for scroll in range(3):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            await self.random_delay(3, 5)
            
            current_jobs = len(self.safe_find_elements(By.CSS_SELECTOR, ".job-card-container, .jobs-search-results__list-item"))
            
            if current_jobs >= target_jobs:
                break
                
            # Cliquer "Voir plus" si disponible
            try:
                see_more = self.safe_find_element(By.CSS_SELECTOR, ".jobs-search-results__pagination button")
                if see_more and see_more.is_enabled():
                    see_more.click()
                    await self.random_delay(3, 5)
            except Exception:
                pass
'''
    
    with open('scrapers/linkedin_scraper.py', 'w', encoding='utf-8') as f:
        f.write(linkedin_content)
    print("✅ scrapers/linkedin_scraper.py créé (RÉEL)")

def main():
    """Créer tous les scrapers Selenium réels"""
    print("🚀 CRÉATION DES SCRAPERS SELENIUM RÉELS")
    print("=" * 50)
    print("⚠️  AUCUN mode démo - uniquement du scraping réel")
    print()
    
    try:
        # Créer la structure
        create_scrapers_directory()
        create_scrapers_init()
        create_base_scraper()
        
        # Créer les scrapers réels
        create_wttj_real_scraper()
        create_indeed_real_scraper()
        create_linkedin_real_scraper()
        
        print("\n✅ CRÉATION TERMINÉE!")
        print("\n📋 Scrapers Selenium RÉELS créés:")
        print("   - scrapers/wttj_scraper.py (WTTJ réel)")
        print("   - scrapers/indeed_scraper.py (Indeed réel)")
        print("   - scrapers/linkedin_scraper.py (LinkedIn réel)")
        
        print("\n🔧 Prochaines étapes:")
        print("   1. Installer Chrome: https://www.google.com/chrome/")
        print("   2. pip install selenium webdriver-manager")
        print("   3. Configurer .env avec LINKEDIN_EMAIL et LINKEDIN_PASSWORD")
        print("   4. Remplacer models/scraper.py par la version réelle")
        print("   5. Tester: python test_scraping.py --quick")
        
        print("\n⚠️  IMPORTANT:")
        print("   - Utilisez un compte LinkedIn dédié au scraping")
        print("   - Respectez les délais anti-détection")
        print("   - Le scraping LinkedIn peut être détecté")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
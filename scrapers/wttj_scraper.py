# scrapers/wttj_scraper.py - Scraper réel pour Welcome to the Jungle avec Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import asyncio
import time
import json
import re
import logging
from typing import List, Dict, Any
from config import Config

logger = logging.getLogger(__name__)

class WTTJScraper:
    """Scraper réel pour Welcome to the Jungle utilisant Selenium"""
    
    def __init__(self):
        self.name = 'Welcome to the Jungle'
        self.base_url = 'https://www.welcometothejungle.com'
        self.search_url = f"{self.base_url}/fr/jobs"
        self.driver = None
        self.wait = None
        
        # Configuration Selenium
        self.setup_selenium_options()
    
    def setup_selenium_options(self):
        """Configure les options Selenium"""
        self.chrome_options = Options()
        
        # Options pour la performance et la discrétion
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent réaliste
        self.chrome_options.add_argument(f'--user-agent={Config.USER_AGENT}')
        
        # Mode headless si configuré
        if Config.SELENIUM_HEADLESS:
            self.chrome_options.add_argument('--headless')
        
        # Langue française
        self.chrome_options.add_argument('--lang=fr-FR')
    
    async def scrape_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Scrape les offres d'emploi de WTTJ"""
        jobs = []
        
        try:
            await self.init_driver()
            
            # Recherche avec différents termes techniques
            search_terms = [
                'développeur', 'data scientist', 'product manager', 
                'devops', 'designer', 'commercial', 'marketing'
            ]
            
            for term in search_terms:
                if len(jobs) >= limit:
                    break
                
                logger.info(f"🔍 Recherche WTTJ pour '{term}'...")
                term_jobs = await self.scrape_search_term(term, min(limit - len(jobs), 20))
                jobs.extend(term_jobs)
                
                # Délai entre recherches
                await asyncio.sleep(Config.REQUEST_DELAY)
            
            logger.info(f"✅ WTTJ: {len(jobs)} offres récupérées")
            return jobs[:limit]
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping WTTJ: {e}")
            return []
        finally:
            await self.close_driver()
    
    async def init_driver(self):
        """Initialise le driver Selenium"""
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            
            # Script pour éviter la détection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("✅ Driver Selenium initialisé")
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation Selenium: {e}")
            raise
    
    async def close_driver(self):
        """Ferme le driver Selenium"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                logger.info("✅ Driver Selenium fermé")
            except Exception as e:
                logger.warning(f"⚠️ Erreur fermeture driver: {e}")
    
    async def scrape_search_term(self, term: str, limit: int) -> List[Dict[str, Any]]:
        """Scrape pour un terme de recherche spécifique"""
        jobs = []
        
        try:
            # Construction de l'URL de recherche
            search_url = f"{self.search_url}?query={term}&refinementList%5Boffices.country_code%5D%5B0%5D=FR"
            
            logger.info(f"📡 Accès à {search_url}")
            self.driver.get(search_url)
            
            # Attendre le chargement de la page
            await asyncio.sleep(3)
            
            # Gestion des cookies si nécessaire
            await self.handle_cookie_banner()
            
            # Attendre que les offres se chargent
            await self.wait_for_job_listings()
            
            # Scraping des offres visibles
            job_links = await self.get_job_links(limit)
            
            logger.info(f"🔗 {len(job_links)} liens d'offres trouvés")
            
            # Scraping détaillé de chaque offre
            for i, job_link in enumerate(job_links):
                if len(jobs) >= limit:
                    break
                
                try:
                    logger.info(f"📄 Scraping offre {i+1}/{len(job_links)}")
                    job_data = await self.scrape_job_detail(job_link)
                    
                    if job_data and job_data.get('title') and job_data.get('company'):
                        jobs.append(job_data)
                    
                    # Délai entre offres
                    await asyncio.sleep(Config.REQUEST_DELAY)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erreur scraping offre {job_link}: {e}")
                    continue
            
            return jobs
            
        except Exception as e:
            logger.error(f"Erreur scraping terme '{term}': {e}")
            return []
    
    async def handle_cookie_banner(self):
        """Gère la bannière de cookies"""
        try:
            # Rechercher le bouton d'acceptation des cookies
            cookie_selectors = [
                "[data-testid='cookie-accept-all']",
                ".cookie-accept",
                "[id*='cookie'][id*='accept']",
                "button[class*='cookie'][class*='accept']"
            ]
            
            for selector in cookie_selectors:
                try:
                    cookie_btn = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    cookie_btn.click()
                    logger.info("✅ Cookies acceptés")
                    await asyncio.sleep(1)
                    return
                except TimeoutException:
                    continue
            
        except Exception as e:
            logger.debug(f"Pas de bannière de cookies ou erreur: {e}")
    
    async def wait_for_job_listings(self):
        """Attend que les offres d'emploi se chargent"""
        try:
            # Sélecteurs possibles pour les offres WTTJ
            job_selectors = [
                "[data-testid='job-search-item']",
                ".job-card",
                "[class*='JobCard']",
                "a[href*='/jobs/']"
            ]
            
            for selector in job_selectors:
                try:
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    logger.info(f"✅ Offres chargées avec sélecteur: {selector}")
                    return
                except TimeoutException:
                    continue
            
            # Si aucun sélecteur ne fonctionne, attendre un peu plus
            await asyncio.sleep(5)
            
        except Exception as e:
            logger.warning(f"⚠️ Timeout attente offres: {e}")
    
    async def get_job_links(self, limit: int) -> List[str]:
        """Récupère les liens vers les offres d'emploi"""
        job_links = []
        
        try:
            # Scroll pour charger plus d'offres
            await self.scroll_to_load_jobs()
            
            # Recherche des liens d'offres
            link_selectors = [
                "a[href*='/jobs/'][href*='/']",
                "[data-testid='job-search-item'] a",
                ".job-card a",
                "a[class*='JobCard']"
            ]
            
            for selector in link_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        href = element.get_attribute('href')
                        if href and '/jobs/' in href and href not in job_links:
                            job_links.append(href)
                            
                            if len(job_links) >= limit:
                                break
                    
                    if job_links:
                        logger.info(f"✅ {len(job_links)} liens trouvés avec {selector}")
                        break
                        
                except Exception as e:
                    logger.debug(f"Sélecteur {selector} échoué: {e}")
                    continue
            
            return job_links[:limit]
            
        except Exception as e:
            logger.error(f"Erreur récupération liens: {e}")
            return []
    
    async def scroll_to_load_jobs(self):
        """Scroll pour charger plus d'offres (lazy loading)"""
        try:
            # Scroll progressif pour déclencher le lazy loading
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            for _ in range(3):  # Maximum 3 scrolls
                # Scroll vers le bas
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                await asyncio.sleep(2)
                
                # Vérifier si de nouveau contenu a été chargé
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
            # Retour en haut
            self.driver.execute_script("window.scrollTo(0, 0);")
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.debug(f"Erreur scroll: {e}")
    
    async def scrape_job_detail(self, job_url: str) -> Dict[str, Any]:
        """Scrape les détails d'une offre d'emploi"""
        try:
            logger.debug(f"📖 Accès à {job_url}")
            self.driver.get(job_url)
            
            # Attendre le chargement de la page
            await asyncio.sleep(2)
            
            # Récupérer le HTML de la page
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extraction des données
            job_data = {
                'url': job_url,
                'source': 'wttj',
                'scraped_at': time.time()
            }
            
            # Titre du poste
            title_selectors = [
                'h1[data-testid="job-title"]',
                'h1.job-title',
                'h1',
                '[class*="JobTitle"]'
            ]
            job_data['title'] = self.extract_text_by_selectors(soup, title_selectors)
            
            # Nom de l'entreprise
            company_selectors = [
                '[data-testid="job-company-name"]',
                '.company-name',
                '[class*="CompanyName"]',
                'a[href*="/companies/"]'
            ]
            job_data['company'] = self.extract_text_by_selectors(soup, company_selectors)
            
            # Localisation
            location_selectors = [
                '[data-testid="job-location"]',
                '.job-location',
                '[class*="Location"]'
            ]
            job_data['location'] = self.extract_text_by_selectors(soup, location_selectors)
            
            # Description du poste
            description_selectors = [
                '[data-testid="job-description"]',
                '.job-description',
                '[class*="JobDescription"]',
                '.content'
            ]
            job_data['description'] = self.extract_text_by_selectors(soup, description_selectors, full_text=True)
            
            # Type de contrat
            contract_selectors = [
                '[data-testid="job-contract-type"]',
                '.contract-type',
                '[class*="ContractType"]'
            ]
            job_data['contract_type'] = self.extract_text_by_selectors(soup, contract_selectors)
            
            # Nettoyage et validation
            if not job_data.get('title') or not job_data.get('company'):
                logger.warning(f"⚠️ Données manquantes pour {job_url}")
                return None
            
            logger.debug(f"✅ Offre scrapée: {job_data['title']} chez {job_data['company']}")
            return job_data
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping détail {job_url}: {e}")
            return None
    
    def extract_text_by_selectors(self, soup: BeautifulSoup, selectors: List[str], full_text: bool = False) -> str:
        """Extrait le texte en essayant plusieurs sélecteurs"""
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True) if not full_text else element.get_text()
                    if text:
                        return text.strip()
            except Exception as e:
                logger.debug(f"Sélecteur {selector} échoué: {e}")
                continue
        
        return ""
    
    def is_driver_available(self) -> bool:
        """Vérifie si le driver Chrome est disponible"""
        try:
            # Test simple de création de driver
            test_options = Options()
            test_options.add_argument('--headless')
            test_options.add_argument('--no-sandbox')
            test_options.add_argument('--disable-dev-shm-usage')
            
            test_driver = webdriver.Chrome(options=test_options)
            test_driver.quit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Chrome WebDriver non disponible: {e}")
            return False


# Version fallback si Selenium n'est pas disponible
class FallbackWTTJScraper:
    """Scraper de fallback sans Selenium (données simulées)"""
    
    def __init__(self):
        self.name = 'Welcome to the Jungle (Fallback)'
    
    async def scrape_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Génère des données simulées si Selenium n'est pas disponible"""
        logger.warning("⚠️ Selenium non disponible, utilisation du fallback avec données simulées")
        
        # Import du générateur de données simulées
        from models.scraper import SimpleWTTJScraper
        simple_scraper = SimpleWTTJScraper()
        
        return await simple_scraper.scrape_jobs(limit)


# Factory pour choisir le bon scraper
def create_wttj_scraper():
    """Factory qui retourne le scraper approprié"""
    try:
        # Vérifier si Selenium et Chrome sont disponibles
        scraper = WTTJScraper()
        if scraper.is_driver_available():
            logger.info("✅ Scraper WTTJ avec Selenium activé")
            return scraper
        else:
            logger.warning("⚠️ Chrome WebDriver non disponible, fallback activé")
            return FallbackWTTJScraper()
            
    except ImportError as e:
        logger.warning(f"⚠️ Selenium non installé ({e}), fallback activé")
        return FallbackWTTJScraper()
    except Exception as e:
        logger.error(f"❌ Erreur création scraper WTTJ: {e}")
        return FallbackWTTJScraper()
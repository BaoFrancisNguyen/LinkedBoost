# scrapers/indeed_scraper.py - Scraper Indeed avec Selenium
import asyncio
import time
import logging
from typing import List, Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from scrapers.base_scraper import BaseScraper
from config import Config
import random
import urllib.parse

logger = logging.getLogger(__name__)

class IndeedScraper(BaseScraper):
    """Scraper Indeed avec Selenium"""
    
    def __init__(self):
        super().__init__('Indeed')
        self.driver = None
        self.base_url = 'https://fr.indeed.com'
        self.search_url = f"{self.base_url}/jobs"
        
    def setup_driver(self) -> webdriver.Chrome:
        """Configure le driver Chrome pour Indeed"""
        options = Options()
        
        # Options anti-détection
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # User agent français
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Fenêtre réaliste
        options.add_argument('--window-size=1920,1080')
        
        # Mode headless si configuré
        if Config.SELENIUM_HEADLESS:
            options.add_argument('--headless')
        
        # Langue française
        options.add_argument('--lang=fr-FR')
        options.add_experimental_option('prefs', {'intl.accept_languages': 'fr-FR,fr'})
        
        try:
            driver = webdriver.Chrome(options=options)
            
            # Masquer les signes d'automation
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return driver
            
        except Exception as e:
            logger.error(f"❌ Erreur création driver Chrome: {e}")
            raise
    
    async def scrape_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Scraping principal des offres Indeed"""
        jobs = []
        search_terms = [
            'développeur python',
            'data scientist',
            'chef de projet digital',
            'développeur web',
            'ingénieur logiciel',
            'consultant IT'
        ]
        
        try:
            self.driver = self.setup_driver()
            logger.info("🔍 Démarrage du scraping Indeed...")
            
            for term in search_terms:
                if len(jobs) >= limit:
                    break
                
                logger.info(f"🔍 Recherche Indeed: '{term}'")
                term_jobs = await self.scrape_jobs_by_term(term, limit - len(jobs))
                jobs.extend(term_jobs)
                
                # Délai entre les recherches
                await self.random_delay(3, 7)
            
            logger.info(f"✅ Indeed: {len(jobs)} offres collectées")
            return jobs[:limit]
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping Indeed: {e}")
            return jobs
        finally:
            if self.driver:
                self.driver.quit()
    
    async def scrape_jobs_by_term(self, search_term: str, max_jobs: int) -> List[Dict[str, Any]]:
        """Scraping pour un terme de recherche spécifique"""
        jobs = []
        
        try:
            # Construction de l'URL de recherche
            params = {
                'q': search_term,
                'l': 'France',
                'sort': 'date',
                'fromage': '7'  # Offres de moins de 7 jours
            }
            
            search_url = f"{self.search_url}?" + urllib.parse.urlencode(params)
            self.driver.get(search_url)
            await self.random_delay(3, 5)
            
            # Accepter les cookies si nécessaire
            await self.handle_cookies_popup()
            
            # Attendre le chargement des résultats
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-jk], .job_seen_beacon"))
                )
            except TimeoutException:
                logger.warning("Timeout en attendant les résultats Indeed")
                return jobs
            
            # Extraction des offres sur plusieurs pages
            page = 1
            max_pages = min(3, (max_jobs // 15) + 1)  # Indeed affiche ~15 offres par page
            
            while page <= max_pages and len(jobs) < max_jobs:
                logger.info(f"📄 Scraping page {page} Indeed...")
                
                # Extraction des offres de la page courante
                page_jobs = await self.extract_jobs_from_page()
                jobs.extend(page_jobs)
                
                if len(page_jobs) == 0:
                    logger.info("Aucune offre trouvée sur cette page, arrêt")
                    break
                
                # Aller à la page suivante
                if page < max_pages and len(jobs) < max_jobs:
                    if await self.go_to_next_page():
                        page += 1
                        await self.random_delay(3, 6)
                    else:
                        break
                else:
                    break
            
            return jobs
            
        except Exception as e:
            logger.error(f"Erreur scraping terme '{search_term}': {e}")
            return jobs
    
    async def extract_jobs_from_page(self) -> List[Dict[str, Any]]:
        """Extraction des offres de la page courante"""
        jobs = []
        
        try:
            # Sélecteurs pour les cartes d'offres Indeed
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, "[data-jk], .job_seen_beacon")
            
            for i, card in enumerate(job_cards):
                try:
                    job_data = await self.extract_job_from_card(card, i)
                    if job_data:
                        jobs.append(job_data)
                        
                    # Délai entre extractions
                    await self.random_delay(0.5, 1.5)
                    
                except Exception as e:
                    logger.debug(f"Erreur extraction job {i}: {e}")
                    continue
            
            logger.info(f"✅ {len(jobs)} offres extraites de cette page")
            return jobs
            
        except Exception as e:
            logger.error(f"Erreur extraction page: {e}")
            return jobs
    
    async def extract_job_from_card(self, job_card, index: int) -> Optional[Dict[str, Any]]:
        """Extraction des données d'une carte d'offre Indeed"""
        try:
            # Titre du poste
            title_elem = job_card.find_element(By.CSS_SELECTOR, "[data-testid='job-title'] a, .jobTitle a")
            title = title_elem.text.strip() if title_elem else ""
            
            # URL de l'offre
            job_url = title_elem.get_attribute('href') if title_elem else ""
            if job_url and not job_url.startswith('http'):
                job_url = self.base_url + job_url
            
            # Entreprise
            try:
                company_elem = job_card.find_element(By.CSS_SELECTOR, "[data-testid='company-name'], .companyName")
                company = company_elem.text.strip()
            except NoSuchElementException:
                company = ""
            
            # Localisation
            try:
                location_elem = job_card.find_element(By.CSS_SELECTOR, "[data-testid='job-location'], .companyLocation")
                location = location_elem.text.strip()
            except NoSuchElementException:
                location = ""
            
            # Résumé/Description courte
            try:
                summary_elem = job_card.find_element(By.CSS_SELECTOR, ".summary, [data-testid='job-snippet']")
                description = summary_elem.text.strip()
            except NoSuchElementException:
                description = ""
            
            # Salaire (si disponible)
            salary = ""
            try:
                salary_elem = job_card.find_element(By.CSS_SELECTOR, ".salary-snippet, [data-testid='job-salary']")
                salary = salary_elem.text.strip()
            except NoSuchElementException:
                pass
            
            # Type de contrat
            contract_type = ""
            try:
                contract_elem = job_card.find_element(By.CSS_SELECTOR, ".jobMetadata, .metadata")
                contract_type = contract_elem.text.strip()
            except NoSuchElementException:
                pass
            
            # Date de publication
            publish_date = ""
            try:
                date_elem = job_card.find_element(By.CSS_SELECTOR, ".date, [data-testid='job-age']")
                publish_date = date_elem.text.strip()
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
                    'publish_date': publish_date,
                    'url': job_url,
                    'source': 'indeed',
                    'scraped_at': time.time()
                }
                
                # Enrichissement avec détails de l'offre (optionnel)
                if job_url:
                    try:
                        detailed_info = await self.get_job_details(job_url)
                        job_data.update(detailed_info)
                    except Exception as e:
                        logger.debug(f"Impossible d'obtenir les détails pour {job_url}: {e}")
                
                return job_data
            
            return None
            
        except Exception as e:
            logger.debug(f"Erreur extraction carte {index}: {e}")
            return None
    
    async def get_job_details(self, job_url: str) -> Dict[str, Any]:
        """Récupère les détails d'une offre (description complète, etc.)"""
        details = {}
        
        try:
            # Ouvrir l'offre dans un nouvel onglet
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[1])
            
            self.driver.get(job_url)
            await self.random_delay(2, 4)
            
            # Description complète
            try:
                desc_elem = self.driver.find_element(By.CSS_SELECTOR, ".jobsearch-jobDescriptionText, #jobDescriptionText")
                details['full_description'] = desc_elem.text.strip()
            except NoSuchElementException:
                pass
            
            # Informations supplémentaires
            try:
                # Type d'emploi
                job_type_elem = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='job-type-label']")
                details['job_type'] = job_type_elem.text.strip()
            except NoSuchElementException:
                pass
            
            # Avantages
            try:
                benefits_elem = self.driver.find_element(By.CSS_SELECTOR, ".benefits, .jobsearch-benefits")
                details['benefits'] = benefits_elem.text.strip()
            except NoSuchElementException:
                pass
            
            # Fermer l'onglet et revenir au principal
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            
            return details
            
        except Exception as e:
            # En cas d'erreur, fermer l'onglet si ouvert et revenir au principal
            if len(self.driver.window_handles) > 1:
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
            
            logger.debug(f"Erreur récupération détails: {e}")
            return details
    
    async def handle_cookies_popup(self):
        """Gestion de la popup de cookies Indeed"""
        try:
            # Attendre et accepter les cookies si nécessaire
            accept_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#onetrust-accept-btn-handler, .gdpr-button-accept"))
            )
            accept_button.click()
            await self.random_delay(1, 2)
            
        except TimeoutException:
            # Pas de popup de cookies
            pass
        except Exception as e:
            logger.debug(f"Erreur gestion cookies: {e}")
    
    async def go_to_next_page(self) -> bool:
        """Navigation vers la page suivante"""
        try:
            # Chercher le bouton "Suivant"
            next_button = self.driver.find_element(By.CSS_SELECTOR, "a[aria-label='Suivant'], a[aria-label='Next']")
            
            if next_button.is_enabled():
                # Scroll vers le bouton
                self.driver.execute_script("arguments[0].scrollIntoView();", next_button)
                await self.random_delay(1, 2)
                
                next_button.click()
                await self.random_delay(3, 5)
                
                return True
            
            return False
            
        except NoSuchElementException:
            logger.info("Pas de page suivante disponible")
            return False
        except Exception as e:
            logger.debug(f"Erreur navigation page suivante: {e}")
            return False
    
    async def random_delay(self, min_seconds: float, max_seconds: float):
        """Délai aléatoire pour simuler un comportement humain"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
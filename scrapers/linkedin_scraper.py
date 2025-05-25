# scrapers/linkedin_scraper.py - Scraper LinkedIn RÉEL avec Selenium
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

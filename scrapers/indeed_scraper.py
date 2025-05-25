# scrapers/indeed_scraper.py - Scraper Indeed RÉEL avec Selenium
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

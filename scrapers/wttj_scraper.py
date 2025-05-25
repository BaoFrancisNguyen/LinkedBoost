# scrapers/wttj_scraper.py - Scraper WTTJ RÉEL avec Selenium
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

# scrapers/linkedin_scraper.py - Scraper LinkedIn pour offres publiques

import time
import logging
import random
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import json
from urllib.parse import urlencode, quote_plus

logger = logging.getLogger(__name__)

class LinkedInScraper:
    """Scraper LinkedIn pour offres publiques - Sans connexion requise"""
    
    def __init__(self):
        self.name = 'LinkedIn Jobs'
        self.base_url = 'https://www.linkedin.com'
        self.jobs_url = 'https://www.linkedin.com/jobs/search'
        self.driver = None
        self.wait = None
        
        # Sélecteurs CSS pour LinkedIn (mis à jour 2025)
        self.selectors = {
            'job_cards': [
                '.job-search-card',
                '.jobs-search__results-list li',
                '[data-entity-urn*="jobPosting"]',
                '.job-result-card',
                '.jobs-search-results__list-item'
            ],
            'job_title': [
                '.job-search-card__title a',
                '.job-result-card__title',
                'h3.job-result-card__title a',
                '.jobs-search-results__list-item h3 a'
            ],
            'company_name': [
                '.job-search-card__subtitle-link',
                '.job-result-card__subtitle',
                '.job-search-card__subtitle',
                'h4 a[data-tracking-control-name="public_jobs_jserp-result_job-search-card-subtitle"]'
            ],
            'location': [
                '.job-search-card__location',
                '.job-result-card__location',
                '.jobs-search-results__list-item .job-result-card__location'
            ],
            'description': [
                '.job-search-card__list-text',
                '.job-result-card__snippet',
                '.jobs-description-content__text'
            ],
            'job_link': [
                '.job-search-card__title a',
                'a[data-tracking-control-name="public_jobs_jserp-result_search-card"]'
            ],
            'load_more_button': [
                'button[aria-label="Voir plus d\'offres d\'emploi"]',
                'button[aria-label="See more jobs"]',
                '.jobs-search-results__pagination button',
                '.artdeco-pagination__button--next'
            ]
        }
    
    def setup_driver(self, headless: bool = False):
        """Configuration du driver Chrome pour LinkedIn"""
        try:
            chrome_options = Options()
            
            if headless:
                chrome_options.add_argument('--headless=new')
            
            # Options anti-détection renforcées pour LinkedIn
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # User agent très réaliste
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Taille de fenêtre réaliste
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--start-maximized')
            
            # Optimisations pour LinkedIn
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-extensions')
            
            # Langue française
            chrome_options.add_argument('--lang=fr-FR')
            chrome_options.add_experimental_option('prefs', {
                'intl.accept_languages': 'fr-FR,fr,en-US,en'
            })
            
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Scripts anti-détection avancés
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['fr-FR', 'fr', 'en-US', 'en']})")
            
            self.wait = WebDriverWait(self.driver, 20)
            
            logger.info("✅ Driver Chrome configuré pour LinkedIn")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur configuration driver LinkedIn: {e}")
            return False
    
    def scrape_jobs(self, limit: int = 200) -> List[Dict[str, Any]]:
        """Scraping principal des offres LinkedIn"""
        jobs = []
        
        if not self.setup_driver(headless=False):
            return []
        
        try:
            # Termes de recherche diversifiés
            search_terms = [
                'développeur', 'developer', 'data scientist', 'chef de projet',
                'product manager', 'marketing', 'commercial', 'ingénieur',
                'consultant', 'analyst', 'designer', 'frontend', 'backend',
                'fullstack', 'devops', 'python', 'javascript', 'react'
            ]
            
            locations = [
                'France', 'Paris', 'Lyon', 'Marseille', 'Toulouse', 
                'Remote', 'Télétravail', 'Lille', 'Nantes'
            ]
            
            for i, term in enumerate(search_terms):
                if len(jobs) >= limit:
                    break
                
                # Alterner les localisations
                location = locations[i % len(locations)]
                
                logger.info(f"🔍 Recherche LinkedIn: '{term}' à {location}")
                term_jobs = self.scrape_search_term(term, location, min(25, limit - len(jobs)))
                jobs.extend(term_jobs)
                
                # Délai anti-détection plus long pour LinkedIn
                time.sleep(random.uniform(5, 10))
            
            logger.info(f"✅ LinkedIn scraping terminé: {len(jobs)} offres trouvées")
            return jobs[:limit]
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping LinkedIn: {e}")
            return jobs
        finally:
            if self.driver:
                self.driver.quit()
    
    def scrape_search_term(self, term: str, location: str, limit: int) -> List[Dict[str, Any]]:
        """Scraping pour un terme de recherche spécifique"""
        jobs = []
        
        try:
            # Construction de l'URL de recherche LinkedIn
            search_params = {
                'keywords': term,
                'location': location,
                'trk': 'public_jobs_jobs-search-bar_search-submit',
                'redirect': 'false',
                'position': '1',
                'pageNum': '0'
            }
            
            search_url = f"{self.jobs_url}?{urlencode(search_params)}"
            
            logger.info(f"🌐 Navigation vers: {search_url}")
            self.driver.get(search_url)
            
            # Attendre le chargement de la page
            time.sleep(random.uniform(3, 6))
            
            # Gérer les pop-ups LinkedIn
            self.handle_linkedin_popups()
            
            # Attendre les résultats
            if not self.wait_for_results():
                logger.warning(f"⚠️ Aucun résultat trouvé pour '{term}' à {location}")
                return []
            
            # Charger plus de résultats
            self.load_more_results(pages=3)  # Charger 3 pages max
            
            # Extraction des offres
            jobs = self.extract_jobs_linkedin(limit)
            
            logger.info(f"📊 Trouvé {len(jobs)} offres pour '{term}' à {location}")
            return jobs
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche LinkedIn '{term}': {e}")
            return []
    
    def handle_linkedin_popups(self):
        """Gérer les pop-ups LinkedIn"""
        try:
            # Pop-up de connexion
            close_selectors = [
                'button[aria-label="Fermer"]',
                'button[aria-label="Close"]',
                '.artdeco-modal__dismiss',
                '.contextual-sign-in-modal__modal-dismiss',
                'button[data-tracking-control-name="public_jobs_contextual-sign-in-modal_modal_dismiss"]'
            ]
            
            for selector in close_selectors:
                try:
                    close_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if close_btn.is_displayed():
                        close_btn.click()
                        logger.info("🔐 Pop-up LinkedIn fermé")
                        time.sleep(1)
                        break
                except:
                    continue
            
            # Pop-up de cookies
            cookie_selectors = [
                'button[action-type="ACCEPT"]',
                'button[data-tracking-control-name="public_jobs_gdpr-banner_accept"]'
            ]
            
            for selector in cookie_selectors:
                try:
                    cookie_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if cookie_btn.is_displayed():
                        cookie_btn.click()
                        logger.info("🍪 Cookies LinkedIn acceptés")
                        time.sleep(1)
                        break
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"Pas de pop-up LinkedIn: {e}")
    
    def wait_for_results(self) -> bool:
        """Attendre que les résultats de recherche se chargent"""
        try:
            # Attendre les cartes d'emploi
            for selector in self.selectors['job_cards']:
                try:
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    logger.info(f"✅ Résultats LinkedIn chargés avec: {selector}")
                    return True
                except TimeoutException:
                    continue
            
            # Vérification alternative
            self.wait.until(lambda driver: len(driver.find_elements(By.CSS_SELECTOR, '[data-entity-urn*="jobPosting"]')) > 0)
            logger.info("✅ Résultats LinkedIn détectés")
            return True
            
        except TimeoutException:
            logger.warning("⚠️ Timeout attente résultats LinkedIn")
            return False
    
    def load_more_results(self, pages: int = 3):
        """Charger plus de résultats en cliquant sur 'Voir plus'"""
        try:
            for page in range(pages):
                # Scroll vers le bas
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Chercher le bouton "Voir plus"
                load_more_found = False
                for selector in self.selectors['load_more_button']:
                    try:
                        load_more_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if load_more_btn.is_displayed() and load_more_btn.is_enabled():
                            self.driver.execute_script("arguments[0].click();", load_more_btn)
                            logger.info(f"📄 Page {page + 2} chargée")
                            load_more_found = True
                            time.sleep(random.uniform(3, 5))
                            break
                    except:
                        continue
                
                if not load_more_found:
                    logger.info("📄 Plus de pages à charger")
                    break
                    
        except Exception as e:
            logger.debug(f"Erreur chargement pages: {e}")
    
    def extract_jobs_linkedin(self, limit: int) -> List[Dict[str, Any]]:
        """Extraction des offres LinkedIn"""
        jobs = []
        
        try:
            # Obtenir toutes les cartes d'emploi
            job_cards = []
            for selector in self.selectors['job_cards']:
                cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if cards:
                    job_cards = cards
                    logger.info(f"🔗 {len(job_cards)} cartes LinkedIn trouvées avec: {selector}")
                    break
            
            if not job_cards:
                logger.warning("❌ Aucune carte d'emploi trouvée")
                return []
            
            # Limiter le nombre de cartes à traiter
            job_cards = job_cards[:min(limit * 2, 100)]
            
            for i, card in enumerate(job_cards):
                try:
                    if len(jobs) >= limit:
                        break
                    
                    job_data = self.extract_job_from_card_linkedin(card)
                    
                    if job_data and job_data.get('title') and job_data.get('company'):
                        jobs.append(job_data)
                        logger.info(f"✅ LinkedIn Job {len(jobs)}: {job_data['title']} - {job_data['company']}")
                    
                except Exception as e:
                    logger.debug(f"Erreur extraction carte LinkedIn {i}: {e}")
                    continue
            
            return jobs
            
        except Exception as e:
            logger.error(f"❌ Erreur extraction LinkedIn: {e}")
            return []
    
    def extract_job_from_card_linkedin(self, card) -> Dict[str, Any]:
        """Extraction des données d'une carte d'emploi LinkedIn"""
        job = {
            'title': '',
            'company': '',
            'location': '',
            'description': '',
            'url': '',
            'source': 'linkedin'
        }
        
        try:
            # Extraction du titre
            for selector in self.selectors['job_title']:
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, selector)
                    if title_elem:
                        job['title'] = title_elem.text.strip()
                        # Récupérer le lien aussi
                        if title_elem.tag_name == 'a':
                            job['url'] = title_elem.get_attribute('href')
                        break
                except:
                    continue
            
            # Si pas de titre trouvé, essayer des méthodes alternatives
            if not job['title']:
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, 'h3')
                    job['title'] = title_elem.text.strip()
                except:
                    pass
            
            # Extraction de l'entreprise
            for selector in self.selectors['company_name']:
                try:
                    company_elem = card.find_element(By.CSS_SELECTOR, selector)
                    if company_elem:
                        job['company'] = company_elem.text.strip()
                        break
                except:
                    continue
            
            # Extraction de la localisation
            for selector in self.selectors['location']:
                try:
                    location_elem = card.find_element(By.CSS_SELECTOR, selector)
                    if location_elem:
                        job['location'] = location_elem.text.strip()
                        break
                except:
                    continue
            
            # Extraction de la description
            for selector in self.selectors['description']:
                try:
                    desc_elem = card.find_element(By.CSS_SELECTOR, selector)
                    if desc_elem:
                        job['description'] = desc_elem.text.strip()
                        break
                except:
                    continue
            
            # Extraction du lien si pas encore trouvé
            if not job['url']:
                for selector in self.selectors['job_link']:
                    try:
                        link_elem = card.find_element(By.CSS_SELECTOR, selector)
                        if link_elem:
                            job['url'] = link_elem.get_attribute('href')
                            break
                    except:
                        continue
            
            # Nettoyage des données
            job = self.clean_job_data_linkedin(job)
            
            return job
            
        except Exception as e:
            logger.debug(f"Erreur extraction job LinkedIn: {e}")
            return job
    
    def clean_job_data_linkedin(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Nettoyage et validation des données LinkedIn"""
        # Nettoyage des espaces et caractères spéciaux
        for key in ['title', 'company', 'location', 'description']:
            if job.get(key):
                job[key] = re.sub(r'\s+', ' ', job[key]).strip()
                job[key] = job[key][:300]  # Limiter la longueur
        
        # Nettoyage des URLs LinkedIn
        if job.get('url'):
            # Nettoyer les paramètres de tracking LinkedIn
            url = job['url']
            if '?' in url:
                url = url.split('?')[0]
            job['url'] = url
        
        # Validation minimale
        if not job.get('title') or len(job['title']) < 3:
            job['title'] = "Poste LinkedIn"
        
        if not job.get('company') or len(job['company']) < 2:
            job['company'] = "Entreprise LinkedIn"
        
        # Ajouter des métadonnées LinkedIn
        job['scraped_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        job['source'] = 'linkedin'
        
        return job
    
    def test_scraper(self):
        """Test du scraper LinkedIn"""
        logger.info("🧪 Test du scraper LinkedIn...")
        jobs = self.scrape_jobs(limit=5)
        
        print(f"\n🎯 TEST LINKEDIN: {len(jobs)} offres extraites")
        for i, job in enumerate(jobs, 1):
            print(f"\n{i}. {job.get('title', 'Sans titre')}")
            print(f"   Entreprise: {job.get('company', 'Non trouvée')}")
            print(f"   Lieu: {job.get('location', 'Non trouvé')}")
            print(f"   URL: {job.get('url', 'Non trouvée')}")
            if job.get('description'):
                print(f"   Description: {job['description'][:100]}...")

# Test du scraper
if __name__ == "__main__":
    scraper = LinkedInScraper()
    scraper.test_scraper()
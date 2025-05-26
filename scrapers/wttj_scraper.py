# scrapers/wttj_scraper.py - FIX pour l'extraction des données

import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import json
import random
import re

logger = logging.getLogger(__name__)

class WTTJScraper:
    """Scraper WTTJ - Version corrigée extraction 2025"""
    
    def __init__(self):
        self.name = 'Welcome to the Jungle'
        self.base_url = 'https://www.welcometothejungle.com'
        self.driver = None
        self.wait = None
    
    def setup_driver(self, headless: bool = False):
        """Configuration du driver Chrome"""
        try:
            chrome_options = Options()
            
            if headless:
                chrome_options.add_argument('--headless=new')
            
            # Options anti-détection
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # User agent réaliste
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebDriver/537.36')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Désactiver les images pour plus de rapidité
            prefs = {"profile.managed_default_content_settings.images": 2}
            chrome_options.add_experimental_option("prefs", prefs)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 15)
            
            logger.info("✅ Driver Chrome configuré avec succès")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur configuration driver: {e}")
            return False
    
    def scrape_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Scraping principal"""
        jobs = []
        
        if not self.setup_driver(headless=False):
            return []
        
        try:
            search_terms = ['développeur', 'data scientist', 'chef de projet', 'commercial']
            
            for term in search_terms:
                if len(jobs) >= limit:
                    break
                
                logger.info(f"🔍 Recherche WTTJ mise à jour: '{term}'")
                term_jobs = self.scrape_search_term_fixed(term, limit - len(jobs))
                jobs.extend(term_jobs)
                
                # Délai anti-détection
                time.sleep(random.uniform(3, 7))
            
            logger.info(f"✅ WTTJ scraping terminé: {len(jobs)} offres trouvées")
            return jobs[:limit]
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping WTTJ: {e}")
            return jobs
        finally:
            if self.driver:
                self.driver.quit()
    
    def scrape_search_term_fixed(self, term: str, limit: int) -> List[Dict[str, Any]]:
        """Méthode de scraping avec extraction CORRIGÉE"""
        jobs = []
        
        try:
            # URL de recherche
            search_url = f"{self.base_url}/fr/jobs?query={term}&refinementList%5Boffices.country_code%5D%5B0%5D=FR"
            
            logger.info(f"🌐 Navigation vers: {search_url}")
            self.driver.get(search_url)
            time.sleep(3)
            
            # Accepter les cookies
            self.handle_cookie_banner()
            
            # Attendre le chargement
            if not self.wait_for_results():
                logger.warning(f"⚠️ Pas de résultats pour '{term}'")
                return []
            
            # Scroll pour charger plus
            self.scroll_to_load_more()
            
            # NOUVELLE MÉTHODE D'EXTRACTION
            jobs = self.extract_jobs_selenium_direct(limit)
            
            logger.info(f"📊 Trouvé {len(jobs)} offres pour '{term}'")
            return jobs
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche '{term}': {e}")
            return []
    
    def extract_jobs_selenium_direct(self, limit: int) -> List[Dict[str, Any]]:
        """EXTRACTION DIRECTE via Selenium - Méthode corrigée"""
        jobs = []
        
        try:
            logger.info("🔍 Extraction directe via Selenium...")
            
            # Stratégie 1: Chercher tous les liens vers /jobs/
            job_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/jobs/"]')
            logger.info(f"🔗 Trouvé {len(job_links)} liens jobs")
            
            # Limiter pour éviter les timeouts
            job_links = job_links[:min(limit * 3, 30)]  # Maximum 30 liens
            
            processed_jobs = []
            
            for i, link in enumerate(job_links):
                try:
                    # Obtenir les informations du lien
                    href = link.get_attribute('href')
                    
                    # Vérifier que c'est bien un lien d'offre
                    if not href or '/jobs/' not in href or href in [job.get('url') for job in processed_jobs]:
                        continue
                    
                    # Extraire les données depuis l'élément parent
                    job_data = self.extract_job_from_selenium_element(link)
                    
                    if job_data and job_data.get('title') and job_data.get('company'):
                        processed_jobs.append(job_data)
                        logger.info(f"✅ Job {len(processed_jobs)}: {job_data['title']} - {job_data['company']}")
                        
                        if len(processed_jobs) >= limit:
                            break
                    
                except Exception as e:
                        logger.debug(f"Erreur extraction job {i}: {e}")
                        continue
            
            logger.info(f"🎯 Extraction terminée: {len(processed_jobs)} offres valides")
            return processed_jobs
            
        except Exception as e:
            logger.error(f"❌ Erreur extraction Selenium: {e}")
            return []
    
    def extract_job_from_selenium_element(self, link_element) -> Dict[str, Any]:
        """Extraction des données depuis un élément Selenium"""
        job = {
            'title': '',
            'company': '',
            'location': '',
            'description': '',
            'url': '',
            'source': 'wttj'
        }
        
        try:
            # URL
            job['url'] = link_element.get_attribute('href')
            
            # Remonter pour trouver la carte parent
            parent_card = self.find_job_card_parent(link_element)
            
            if parent_card:
                # Extraction du titre
                job['title'] = self.extract_title_from_card(parent_card, link_element)
                
                # Extraction de l'entreprise
                job['company'] = self.extract_company_from_card(parent_card)
                
                # Extraction de la localisation
                job['location'] = self.extract_location_from_card(parent_card)
                
                # Description courte si disponible
                job['description'] = self.extract_description_from_card(parent_card)
            
            # Si pas de titre, utiliser le texte du lien
            if not job['title']:
                job['title'] = link_element.text.strip()
            
            # Nettoyage des données
            job = self.clean_job_data(job)
            
            return job
            
        except Exception as e:
            logger.debug(f"Erreur extraction élément: {e}")
            return job
    
    def find_job_card_parent(self, link_element):
        """Trouve l'élément parent qui contient toute la carte job"""
        try:
            # Essayer différents niveaux de parents
            current = link_element
            
            for level in range(5):  # Remonter jusqu'à 5 niveaux
                current = current.find_element(By.XPATH, "..")
                
                # Vérifier si c'est une carte job (contient plusieurs informations)
                text_content = current.text
                
                # Critères pour identifier une carte job
                if (len(text_content) > 50 and  # Contenu substantiel
                    any(keyword in text_content.lower() for keyword in ['cdi', 'stage', 'temps', 'salaire', '€', 'paris', 'lyon', 'remote']) and
                    len(current.find_elements(By.CSS_SELECTOR, '*')) > 3):  # Plusieurs sous-éléments
                    
                    return current
            
            return link_element.find_element(By.XPATH, "..")  # Au minimum le parent direct
            
        except:
            return None
    
    def extract_title_from_card(self, card, link_element) -> str:
        """Extraction du titre depuis la carte"""
        try:
            # Priorité 1: Texte du lien lui-même
            link_text = link_element.text.strip()
            if link_text and len(link_text) > 5 and not link_text.lower() in ['voir', 'details', 'postuler']:
                return link_text
            
            # Priorité 2: Titre/attributs du lien
            title_attr = link_element.get_attribute('title')
            if title_attr:
                return title_attr.strip()
            
            # Priorité 3: Headers dans la carte
            for tag in ['h1', 'h2', 'h3', 'h4']:
                headers = card.find_elements(By.TAG_NAME, tag)
                for header in headers:
                    header_text = header.text.strip()
                    if header_text and len(header_text) > 5:
                        return header_text
            
            # Priorité 4: Éléments avec classes contenant "title" ou "job"
            for selector in ['[class*="title"]', '[class*="Title"]', '[class*="job"]']:
                try:
                    elements = card.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        text = elem.text.strip()
                        if text and len(text) > 5 and len(text) < 100:
                            return text
                except:
                    continue
            
            return ""
            
        except Exception as e:
            logger.debug(f"Erreur extraction titre: {e}")
            return ""
    
    def extract_company_from_card(self, card) -> str:
        """Extraction de l'entreprise depuis la carte"""
        try:
            # Chercher des éléments avec "company" dans la classe
            for selector in ['[class*="company"]', '[class*="Company"]', '[class*="organization"]']:
                try:
                    elements = card.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        text = elem.text.strip()
                        if text and len(text) > 1 and len(text) < 50:
                            return text
                except:
                    continue
            
            # Fallback: chercher dans le texte global
            full_text = card.text
            lines = [line.strip() for line in full_text.split('\n') if line.strip()]
            
            # La compagnie est souvent sur la 2ème ou 3ème ligne
            for line in lines[1:4]:
                if (len(line) > 1 and len(line) < 50 and 
                    not any(keyword in line.lower() for keyword in ['cdi', 'stage', 'temps', 'il y a', 'jour', 'semaine'])):
                    return line
            
            return ""
            
        except Exception as e:
            logger.debug(f"Erreur extraction entreprise: {e}")
            return ""
    
    def extract_location_from_card(self, card) -> str:
        """Extraction de la localisation depuis la carte"""
        try:
            # Chercher des éléments avec "location" dans la classe
            for selector in ['[class*="location"]', '[class*="Location"]', '[class*="place"]']:
                try:
                    elements = card.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        text = elem.text.strip()
                        if text and any(city in text for city in ['Paris', 'Lyon', 'Marseille', 'Toulouse', 'France', 'Remote']):
                            return text
                except:
                    continue
            
            # Fallback: chercher dans le texte
            full_text = card.text.lower()
            cities = ['paris', 'lyon', 'marseille', 'toulouse', 'lille', 'nantes', 'strasbourg', 'bordeaux', 'remote', 'télétravail']
            
            for city in cities:
                if city in full_text:
                    # Extraire la ligne contenant la ville
                    lines = card.text.split('\n')
                    for line in lines:
                        if city in line.lower():
                            return line.strip()
            
            return ""
            
        except Exception as e:
            logger.debug(f"Erreur extraction localisation: {e}")
            return ""
    
    def extract_description_from_card(self, card) -> str:
        """Extraction de description courte depuis la carte"""
        try:
            # Chercher des éléments de description
            for selector in ['[class*="description"]', '[class*="summary"]', 'p']:
                try:
                    elements = card.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        text = elem.text.strip()
                        if text and len(text) > 20 and len(text) < 200:
                            return text
                except:
                    continue
            
            return ""
            
        except Exception as e:
            logger.debug(f"Erreur extraction description: {e}")
            return ""
    
    def clean_job_data(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Nettoyage et validation des données job"""
        # Nettoyage des espaces et caractères spéciaux
        for key in ['title', 'company', 'location', 'description']:
            if job.get(key):
                job[key] = re.sub(r'\s+', ' ', job[key]).strip()
                job[key] = job[key][:200]  # Limiter la longueur
        
        # Validation URL
        if job.get('url') and not job['url'].startswith('http'):
            if job['url'].startswith('/'):
                job['url'] = f"{self.base_url}{job['url']}"
        
        # Validation minimale
        if not job.get('title') or len(job['title']) < 5:
            job['title'] = "Poste à définir"
        
        if not job.get('company') or len(job['company']) < 2:
            job['company'] = "Entreprise"
        
        return job
    
    def handle_cookie_banner(self):
        """Gestion des cookies"""
        cookie_selectors = [
            '[data-testid="cookie-banner-accept"]',
            '#didomi-notice-agree-button',
            '.cookie-accept',
            'button[id*="accept"]',
            'button[class*="accept"]',
            'button:contains("Accepter")',
            'button:contains("Accept")'
        ]
        
        for selector in cookie_selectors:
            try:
                cookie_btn = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                cookie_btn.click()
                logger.info("🍪 Cookies acceptés")
                time.sleep(1)
                return
            except TimeoutException:
                continue
        
        # Essayer avec XPath pour les textes
        try:
            cookie_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Accepter') or contains(text(), 'Accept')]")
            cookie_btn.click()
            logger.info("🍪 Cookies acceptés via XPath")
        except:
            logger.debug("Pas de bannière cookie trouvée")
    
    def wait_for_results(self) -> bool:
        """Attente des résultats"""
        try:
            # Attendre que la page soit chargée
            self.wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            
            # Attendre un minimum de contenu
            time.sleep(3)
            
            # Vérifier la présence de liens jobs
            job_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/jobs/"]')
            
            if len(job_links) > 0:
                logger.info(f"✅ {len(job_links)} liens jobs détectés")
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Erreur attente résultats: {e}")
            return False
    
    def scroll_to_load_more(self):
        """Scroll pour charger plus de résultats"""
        try:
            initial_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Scroll progressif
            for i in range(2):  # Réduire à 2 scrolls
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == initial_height:
                    break
                initial_height = new_height
                
        except Exception as e:
            logger.debug(f"Erreur scroll: {e}")

# Test rapide
def test_extraction():
    """Test de l'extraction corrigée"""
    scraper = WTTJScraper()
    jobs = scraper.scrape_jobs(limit=3)
    
    print(f"\n🎯 RÉSULTATS TEST: {len(jobs)} offres extraites")
    for i, job in enumerate(jobs, 1):
        print(f"\n{i}. {job.get('title', 'Sans titre')}")
        print(f"   Entreprise: {job.get('company', 'Non trouvée')}")
        print(f"   Lieu: {job.get('location', 'Non trouvé')}")
        print(f"   URL: {job.get('url', 'Non trouvée')}")

if __name__ == "__main__":
    test_extraction()
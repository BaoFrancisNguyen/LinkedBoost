# scrapers/base_scraper.py - Classe de base pour scrapers Selenium RÉELS
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

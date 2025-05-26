# config.py - Configuration complète pour LinkedBoost avec Selenium
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Configuration de base
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'linkedboost-dev-key'
    OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL') or 'http://localhost:11434'
    OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL') or 'mistral:latest'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Configuration scraping Selenium
    SCRAPING_ENABLED = os.environ.get('SCRAPING_ENABLED', 'True').lower() == 'true'
    SCRAPING_INTERVAL_HOURS = int(os.environ.get('SCRAPING_INTERVAL_HOURS', 24))
    MAX_JOBS_PER_SCRAPE = int(os.environ.get('MAX_JOBS_PER_SCRAPE', 50))
    
    # Configuration Selenium
    SELENIUM_HEADLESS = os.environ.get('SELENIUM_HEADLESS', 'False').lower() == 'False'
    SELENIUM_TIMEOUT = int(os.environ.get('SELENIUM_TIMEOUT', 300))
    SELENIUM_PAGE_LOAD_TIMEOUT = int(os.environ.get('SELENIUM_PAGE_LOAD_TIMEOUT', 45))
    SELENIUM_IMPLICIT_WAIT = int(os.environ.get('SELENIUM_IMPLICIT_WAIT', 10))
    
    # User Agent
    USER_AGENT = os.environ.get('USER_AGENT') or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
    # Credentials LinkedIn
    LINKEDIN_EMAIL = os.environ.get('LINKEDIN_EMAIL', '')
    LINKEDIN_PASSWORD = os.environ.get('LINKEDIN_PASSWORD', '')
    
    # Rate limiting
    REQUEST_DELAY = float(os.environ.get('REQUEST_DELAY', 2.0))
    RANDOM_DELAY_MIN = float(os.environ.get('RANDOM_DELAY_MIN', 1.0))
    RANDOM_DELAY_MAX = float(os.environ.get('RANDOM_DELAY_MAX', 5.0))
    CONCURRENT_REQUESTS = int(os.environ.get('CONCURRENT_REQUESTS', 1))
    
    # Configuration Chrome
    CHROME_OPTIONS = {
        'window_size': os.environ.get('CHROME_WINDOW_SIZE', '1920,1080'),
        'disable_images': os.environ.get('CHROME_DISABLE_IMAGES', 'False').lower() == 'true',
        'disable_gpu': os.environ.get('CHROME_DISABLE_GPU', 'True').lower() == 'true',
        'no_sandbox': os.environ.get('CHROME_NO_SANDBOX', 'True').lower() == 'true'
    }
    
    # Base de données
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///data/linkedboost.db'
    
    # Chemins
    DATA_DIR = os.environ.get('DATA_DIR') or './data'
    REPORTS_DIR = os.environ.get('REPORTS_DIR') or './data/reports'
    LOGS_DIR = os.environ.get('LOGS_DIR') or './logs'
    
    # Configuration de logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_TO_FILE = os.environ.get('LOG_TO_FILE', 'True').lower() == 'true'
    
    # Sources de scraping
    ENABLED_SCRAPERS = os.environ.get('ENABLED_SCRAPERS', 'wttj,indeed').split(',')
    
    # Limites par source
    WTTJ_MAX_JOBS = int(os.environ.get('WTTJ_MAX_JOBS', 30))
    INDEED_MAX_JOBS = int(os.environ.get('INDEED_MAX_JOBS', 20))
    LINKEDIN_MAX_JOBS = int(os.environ.get('LINKEDIN_MAX_JOBS', 15))
    
    # Seuils
    MAX_PAGES_PER_SEARCH = int(os.environ.get('MAX_PAGES_PER_SEARCH', 3))
    MAX_DAILY_REQUESTS = int(os.environ.get('MAX_DAILY_REQUESTS', 1000))
    COOLDOWN_AFTER_ERROR = int(os.environ.get('COOLDOWN_AFTER_ERROR', 60))
    
    @classmethod
    def get_chrome_options(cls):
        """Retourne les options Chrome configurées"""
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        
        # Mode headless ou visible
        if cls.SELENIUM_HEADLESS:
            options.add_argument('--headless')
            print("🔧 Mode HEADLESS: Navigateur invisible")
        else:
            print("🔧 Mode VISIBLE: Navigateur sera affiché")
        
        # Configuration de base
        options.add_argument(f'--user-agent={cls.USER_AGENT}')
        options.add_argument(f'--window-size={cls.CHROME_OPTIONS["window_size"]}')
        
        # Options anti-détection
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Performance et sécurité
        if cls.CHROME_OPTIONS['no_sandbox']:
            options.add_argument('--no-sandbox')
        
        if cls.CHROME_OPTIONS['disable_gpu']:
            options.add_argument('--disable-gpu')
            
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        
        # Images
        if cls.CHROME_OPTIONS['disable_images']:
            prefs = {"profile.managed_default_content_settings.images": 2}
            options.add_experimental_option("prefs", prefs)
        
        # Langue française
        options.add_argument('--lang=fr-FR')
        options.add_experimental_option('prefs', {'intl.accept_languages': 'fr-FR,fr'})
        
        return options
    
    @classmethod
    def validate_config(cls):
        """Valide la configuration"""
        errors = []
        
        if cls.MAX_JOBS_PER_SCRAPE <= 0:
            errors.append("MAX_JOBS_PER_SCRAPE doit être positif")
        
        if cls.REQUEST_DELAY < 0:
            errors.append("REQUEST_DELAY doit être positif ou nul")
        
        if cls.LINKEDIN_EMAIL and not cls.LINKEDIN_PASSWORD:
            errors.append("LINKEDIN_PASSWORD requis si LINKEDIN_EMAIL est défini")
        
        # Vérifications des répertoires
        for directory in [cls.DATA_DIR, cls.REPORTS_DIR, cls.LOGS_DIR]:
            try:
                os.makedirs(directory, exist_ok=True)
            except Exception as e:
                errors.append(f"Impossible de créer le répertoire {directory}: {e}")
        
        return errors
    
    @classmethod
    def enable_debug_mode(cls):
        """Active le mode debug avec navigateur visible"""
        os.environ['SELENIUM_HEADLESS'] = 'False'
        os.environ['REQUEST_DELAY'] = '3.0'
        os.environ['RANDOM_DELAY_MIN'] = '2.0'
        os.environ['RANDOM_DELAY_MAX'] = '5.0'
        
        # Recharger la configuration
        cls.SELENIUM_HEADLESS = False
        cls.REQUEST_DELAY = 3.0
        cls.RANDOM_DELAY_MIN = 2.0
        cls.RANDOM_DELAY_MAX = 5.0
        
        print("🔧 Mode DEBUG activé:")
        print("   - Navigateur VISIBLE")
        print("   - Délais LENTS pour observation")
        print("   - Logs détaillés")
    
    @classmethod
    def get_scraper_config(cls, scraper_name: str) -> dict:
        """Retourne la configuration spécifique à un scraper"""
        configs = {
            'wttj': {
                'max_jobs': cls.WTTJ_MAX_JOBS,
                'base_url': 'https://www.welcometothejungle.com',
                'search_terms': ['développeur', 'data', 'marketing', 'commercial']
            },
            'indeed': {
                'max_jobs': cls.INDEED_MAX_JOBS,
                'base_url': 'https://fr.indeed.com',
                'search_terms': ['développeur python', 'data scientist', 'chef de projet']
            },
            'linkedin': {
                'max_jobs': cls.LINKEDIN_MAX_JOBS,
                'base_url': 'https://www.linkedin.com',
                'search_terms': ['développeur', 'data scientist', 'chef de projet digital'],
                'requires_auth': True
            }
        }
        
        return configs.get(scraper_name, {})
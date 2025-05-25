# config.py - Configuration complète pour LinkedBoost
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class Config:
    """Configuration de base pour LinkedBoost"""
    
    # ===========================
    # CONFIGURATION FLASK
    # ===========================
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'linkedboost-dev-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    PORT = int(os.environ.get('FLASK_PORT', 5000))
    
    # ===========================
    # CONFIGURATION OLLAMA
    # ===========================
    OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'mistral:latest')
    OLLAMA_TIMEOUT = int(os.environ.get('OLLAMA_TIMEOUT', 60))
    
    # Modèles d'embeddings
    OLLAMA_EMBEDDING_MODEL = os.environ.get('OLLAMA_EMBEDDING_MODEL', 'nomic-embed-text:latest')
    
    # ===========================
    # CONFIGURATION SCRAPING
    # ===========================
    SCRAPING_ENABLED = os.environ.get('SCRAPING_ENABLED', 'True').lower() == 'true'
    SCRAPING_INTERVAL_HOURS = int(os.environ.get('SCRAPING_INTERVAL_HOURS', 24))
    MAX_JOBS_PER_SCRAPE = int(os.environ.get('MAX_JOBS_PER_SCRAPE', 100))
    
    # Rate limiting pour le scraping
    REQUEST_DELAY = float(os.environ.get('REQUEST_DELAY', 2.0))  # Secondes entre requêtes
    CONCURRENT_REQUESTS = int(os.environ.get('CONCURRENT_REQUESTS', 1))  # Requêtes simultanées
    
    # Retry et timeouts
    MAX_RETRIES = int(os.environ.get('MAX_RETRIES', 3))
    SCRAPING_TIMEOUT = int(os.environ.get('SCRAPING_TIMEOUT', 30))
    
    # ===========================
    # CONFIGURATION SELENIUM
    # ===========================
    SELENIUM_HEADLESS = os.environ.get('SELENIUM_HEADLESS', 'True').lower() == 'true'
    SELENIUM_TIMEOUT = int(os.environ.get('SELENIUM_TIMEOUT', 10))
    SELENIUM_PAGE_LOAD_TIMEOUT = int(os.environ.get('SELENIUM_PAGE_LOAD_TIMEOUT', 30))
    SELENIUM_IMPLICIT_WAIT = int(os.environ.get('SELENIUM_IMPLICIT_WAIT', 5))
    
    # User Agent pour le scraping
    USER_AGENT = os.environ.get('USER_AGENT', 
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Chrome options avancées
    CHROME_BINARY_PATH = os.environ.get('CHROME_BINARY_PATH')  # Chemin custom vers Chrome
    CHROMEDRIVER_PATH = os.environ.get('CHROMEDRIVER_PATH')   # Chemin custom vers ChromeDriver
    
    # ===========================
    # CONFIGURATION BASE DE DONNÉES
    # ===========================
    # Base de données principale
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///data/linkedboost.db')
    
    # Base de données pour les embeddings
    EMBEDDINGS_DB_PATH = os.environ.get('EMBEDDINGS_DB_PATH', 'data/embeddings.db')
    
    # Base de données pour la recherche simple
    SIMPLE_SEARCH_DB_PATH = os.environ.get('SIMPLE_SEARCH_DB_PATH', 'data/simple_search.db')
    
    # ChromaDB (pour les embeddings vectoriels)
    CHROMA_DB_PATH = os.environ.get('CHROMA_DB_PATH', 'data/chroma_db')
    CHROMA_COLLECTION_NAME = os.environ.get('CHROMA_COLLECTION_NAME', 'linkedboost_jobs')
    
    # ===========================
    # CONFIGURATION EMBEDDINGS & RAG
    # ===========================
    # Modèle d'embeddings (sentence-transformers)
    EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    
    # Méthode de recherche ('ollama', 'tfidf', 'sentence_transformers')
    SEARCH_METHOD = os.environ.get('SEARCH_METHOD', 'auto')  # auto = détection automatique
    
    # Paramètres de recherche
    SEARCH_SIMILARITY_THRESHOLD = float(os.environ.get('SEARCH_SIMILARITY_THRESHOLD', 0.7))
    MAX_SEARCH_RESULTS = int(os.environ.get('MAX_SEARCH_RESULTS', 20))
    
    # Cache des embeddings
    CACHE_EMBEDDINGS = os.environ.get('CACHE_EMBEDDINGS', 'True').lower() == 'true'
    EMBEDDING_CACHE_SIZE = int(os.environ.get('EMBEDDING_CACHE_SIZE', 1000))
    
    # ===========================
    # CONFIGURATION LOGGING
    # ===========================
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/linkedboost.log')
    LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 5))
    
    # Logs spécifiques
    SCRAPING_LOG_FILE = os.environ.get('SCRAPING_LOG_FILE', 'logs/scraping.log')
    ERROR_LOG_FILE = os.environ.get('ERROR_LOG_FILE', 'logs/errors.log')
    
    # ===========================
    # CONFIGURATION SÉCURITÉ
    # ===========================
    # Protection CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # Rate limiting API
    API_RATE_LIMIT = os.environ.get('API_RATE_LIMIT', '100 per hour')
    API_RATE_LIMIT_STORAGE_URL = os.environ.get('API_RATE_LIMIT_STORAGE_URL')
    
    # Admin access (optionnel)
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')  # Si défini, protège l'admin
    
    # ===========================
    # CONFIGURATION CACHE
    # ===========================
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')  # simple, redis, filesystem
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))  # 5 minutes
    
    # Redis (si utilisé)
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # ===========================
    # CONFIGURATION BUSINESS
    # ===========================
    # Paramètres de génération IA
    DEFAULT_TEMPERATURE = float(os.environ.get('DEFAULT_TEMPERATURE', 0.7))
    DEFAULT_MAX_TOKENS = int(os.environ.get('DEFAULT_MAX_TOKENS', 500))
    
    # Limites utilisateur
    MAX_GENERATIONS_PER_HOUR = int(os.environ.get('MAX_GENERATIONS_PER_HOUR', 50))
    MAX_PROFILE_ANALYSIS_PER_DAY = int(os.environ.get('MAX_PROFILE_ANALYSIS_PER_DAY', 10))
    
    # ===========================
    # CONFIGURATION MONITORING
    # ===========================
    HEALTH_CHECK_INTERVAL = int(os.environ.get('HEALTH_CHECK_INTERVAL', 30))  # secondes
    METRICS_ENABLED = os.environ.get('METRICS_ENABLED', 'True').lower() == 'true'
    
    # Alertes (optionnel)
    ALERT_EMAIL = os.environ.get('ALERT_EMAIL')
    SMTP_SERVER = os.environ.get('SMTP_SERVER')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
    
    # ===========================
    # CONFIGURATION SOURCES DE SCRAPING
    # ===========================
    # Sources activées
    ENABLED_SCRAPERS = os.environ.get('ENABLED_SCRAPERS', 'wttj').split(',')
    
    # Configuration spécifique WTTJ
    WTTJ_MAX_PAGES = int(os.environ.get('WTTJ_MAX_PAGES', 5))
    WTTJ_SEARCH_TERMS = os.environ.get('WTTJ_SEARCH_TERMS', 
        'développeur,data,marketing,commercial,product').split(',')
    
    # Configuration LinkedIn (future)
    LINKEDIN_ENABLED = os.environ.get('LINKEDIN_ENABLED', 'False').lower() == 'true'
    LINKEDIN_USERNAME = os.environ.get('LINKEDIN_USERNAME')
    LINKEDIN_PASSWORD = os.environ.get('LINKEDIN_PASSWORD')
    
    # Configuration Indeed (future)
    INDEED_ENABLED = os.environ.get('INDEED_ENABLED', 'False').lower() == 'true'
    INDEED_LOCATION = os.environ.get('INDEED_LOCATION', 'France')
    
    # ===========================
    # MÉTHODES UTILITAIRES
    # ===========================
    
    @classmethod
    def get_database_config(cls):
        """Retourne la configuration de base de données"""
        return {
            'main_db': cls.DATABASE_URL,
            'embeddings_db': cls.EMBEDDINGS_DB_PATH,
            'search_db': cls.SIMPLE_SEARCH_DB_PATH,
            'chroma_db': cls.CHROMA_DB_PATH
        }
    
    @classmethod
    def get_ollama_config(cls):
        """Retourne la configuration Ollama"""
        return {
            'base_url': cls.OLLAMA_BASE_URL,
            'model': cls.OLLAMA_MODEL,
            'embedding_model': cls.OLLAMA_EMBEDDING_MODEL,
            'timeout': cls.OLLAMA_TIMEOUT
        }
    
    @classmethod
    def get_selenium_config(cls):
        """Retourne la configuration Selenium"""
        return {
            'headless': cls.SELENIUM_HEADLESS,
            'timeout': cls.SELENIUM_TIMEOUT,
            'page_load_timeout': cls.SELENIUM_PAGE_LOAD_TIMEOUT,
            'implicit_wait': cls.SELENIUM_IMPLICIT_WAIT,
            'user_agent': cls.USER_AGENT,
            'chrome_binary': cls.CHROME_BINARY_PATH,
            'chromedriver_path': cls.CHROMEDRIVER_PATH
        }
    
    @classmethod
    def get_scraping_config(cls):
        """Retourne la configuration de scraping"""
        return {
            'enabled': cls.SCRAPING_ENABLED,
            'interval_hours': cls.SCRAPING_INTERVAL_HOURS,
            'max_jobs': cls.MAX_JOBS_PER_SCRAPE,
            'request_delay': cls.REQUEST_DELAY,
            'concurrent_requests': cls.CONCURRENT_REQUESTS,
            'max_retries': cls.MAX_RETRIES,
            'timeout': cls.SCRAPING_TIMEOUT,
            'enabled_scrapers': cls.ENABLED_SCRAPERS
        }
    
    @classmethod
    def validate_config(cls):
        """Valide la configuration et retourne les erreurs"""
        errors = []
        warnings = []
        
        # Vérifications critiques
        if not cls.SECRET_KEY or cls.SECRET_KEY == 'linkedboost-dev-key-change-in-production':
            if not cls.DEBUG:
                errors.append("SECRET_KEY doit être définie en production")
            else:
                warnings.append("SECRET_KEY par défaut utilisée en développement")
        
        # Vérifications Ollama
        if not cls.OLLAMA_BASE_URL:
            errors.append("OLLAMA_BASE_URL est requis")
        
        if not cls.OLLAMA_MODEL:
            errors.append("OLLAMA_MODEL est requis")
        
        # Vérifications scraping
        if cls.SCRAPING_ENABLED and not cls.ENABLED_SCRAPERS:
            warnings.append("Scraping activé mais aucun scraper configuré")
        
        if cls.REQUEST_DELAY < 1.0:
            warnings.append("REQUEST_DELAY < 1s peut causer des blocages")
        
        # Vérifications base de données
        if 'sqlite' in cls.DATABASE_URL.lower():
            import os
            db_dir = os.path.dirname(cls.DATABASE_URL.replace('sqlite:///', ''))
            if db_dir and not os.path.exists(db_dir):
                warnings.append(f"Répertoire base de données n'existe pas: {db_dir}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    @classmethod
    def get_config_summary(cls):
        """Retourne un résumé de la configuration"""
        return {
            'environment': 'development' if cls.DEBUG else 'production',
            'ollama_model': cls.OLLAMA_MODEL,
            'scraping_enabled': cls.SCRAPING_ENABLED,
            'selenium_headless': cls.SELENIUM_HEADLESS,
            'enabled_scrapers': cls.ENABLED_SCRAPERS,
            'search_method': cls.SEARCH_METHOD,
            'database_type': 'sqlite' if 'sqlite' in cls.DATABASE_URL else 'other'
        }


class DevelopmentConfig(Config):
    """Configuration pour le développement"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    SELENIUM_HEADLESS = False  # Voir le navigateur en dev
    REQUEST_DELAY = 1.0  # Plus rapide en dev
    SCRAPING_INTERVAL_HOURS = 1  # Scraping plus fréquent
    

class ProductionConfig(Config):
    """Configuration pour la production"""
    DEBUG = False
    LOG_LEVEL = 'INFO'
    SELENIUM_HEADLESS = True
    REQUEST_DELAY = 3.0  # Plus respectueux en prod
    SCRAPING_INTERVAL_HOURS = 24
    
    # Sécurité renforcée
    CORS_ORIGINS = ['https://your-domain.com']
    API_RATE_LIMIT = '50 per hour'


class TestingConfig(Config):
    """Configuration pour les tests"""
    TESTING = True
    DEBUG = True
    DATABASE_URL = 'sqlite:///:memory:'
    SCRAPING_ENABLED = False
    SELENIUM_HEADLESS = True


# Factory de configuration
def get_config(environment=None):
    """Retourne la configuration selon l'environnement"""
    if environment is None:
        environment = os.environ.get('FLASK_ENV', 'development')
    
    configs = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig
    }
    
    return configs.get(environment, DevelopmentConfig)


# Configuration globale (pour compatibilité)
Config = get_config()
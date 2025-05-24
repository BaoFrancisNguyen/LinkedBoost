# config.py - Configuration étendue
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Configuration existante
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'linkedboost-dev-key'
    OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL') or 'http://localhost:11434'
    OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL') or 'mistral:latest'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Nouvelle configuration scraping
    SCRAPING_ENABLED = os.environ.get('SCRAPING_ENABLED', 'True').lower() == 'true'
    SCRAPING_INTERVAL_HOURS = int(os.environ.get('SCRAPING_INTERVAL_HOURS', 24))
    MAX_JOBS_PER_SCRAPE = int(os.environ.get('MAX_JOBS_PER_SCRAPE', 100))
    
    # Base de données
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///linkedboost.db'
    CHROMA_DB_PATH = os.environ.get('CHROMA_DB_PATH') or './data/chroma_db'
    
    # Modèle d'embeddings
    EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL') or 'all-MiniLM-L6-v2'
    
    # Configuration scrapers
    SELENIUM_HEADLESS = os.environ.get('SELENIUM_HEADLESS', 'True').lower() == 'true'
    USER_AGENT = 'LinkedBoost/1.0 (Educational Purpose)'
    
    # Rate limiting
    REQUEST_DELAY = float(os.environ.get('REQUEST_DELAY', 2.0))  # secondes entre requêtes
    CONCURRENT_REQUESTS = int(os.environ.get('CONCURRENT_REQUESTS', 3))
# scrapers/__init__.py
"""
Modules de scraping pour LinkedBoost
"""

__version__ = "1.0.0"
__author__ = "LinkedBoost Team"

# Import des scrapers disponibles
try:
    from .base_scraper import BaseScraper
    from .wttj_scraper import WTTJScraper
    SCRAPERS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Erreur import scrapers: {e}")
    SCRAPERS_AVAILABLE = False

# Liste des scrapers supportés
SUPPORTED_SCRAPERS = {
    'wttj': 'WTTJScraper',
    'linkedin': 'LinkedInScraper',  # À venir
    'indeed': 'IndeedScraper'       # À venir
}

def get_available_scrapers():
    """Retourne la liste des scrapers disponibles"""
    available = []
    
    if SCRAPERS_AVAILABLE:
        try:
            from .wttj_scraper import WTTJScraper
            available.append('wttj')
        except ImportError:
            pass
    
    return available

def create_scraper(scraper_name: str):
    """Factory pour créer un scraper"""
    if scraper_name == 'wttj':
        try:
            from .wttj_scraper import WTTJScraper
            return WTTJScraper()
        except ImportError:
            raise ImportError(f"Scraper {scraper_name} non disponible")
    
    raise ValueError(f"Scraper {scraper_name} non supporté")
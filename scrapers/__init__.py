# scrapers/__init__.py
"""
Package de scrapers RÉELS pour LinkedBoost
Aucun mode démo - uniquement du scraping Selenium réel
"""

__version__ = "1.0.0"
__all__ = []

# Import des scrapers réels disponibles
try:
    from .wttj_scraper import WTTJScraper
    __all__.append('WTTJScraper')
except ImportError:
    pass

try:
    from .linkedin_scraper import LinkedInScraper
    __all__.append('LinkedInScraper')
except ImportError:
    pass

try:
    from .indeed_scraper import IndeedScraper
    __all__.append('IndeedScraper')
except ImportError:
    pass

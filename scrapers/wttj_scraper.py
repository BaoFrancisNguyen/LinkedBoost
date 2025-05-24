# scrapers/wttj_scraper.py - Scraper Welcome to the Jungle
from scrapers.base_scraper import BaseScraper
from bs4 import BeautifulSoup
import json
import logging

logger = logging.getLogger(__name__)

class WTTJScraper(BaseScraper):
    """Scraper pour Welcome to the Jungle"""
    
    def __init__(self):
        super().__init__('Welcome to the Jungle')
        self.base_url = 'https://www.welcometothejungle.com'
        self.search_url = f"{self.base_url}/fr/jobs"
    
    async def scrape_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Scrape les offres d'emploi de WTTJ"""
        jobs = []
        
        try:
            # Recherche avec différents termes
            search_terms = ['développeur', 'data', 'marketing', 'commercial']
            
            for term in search_terms:
                if len(jobs) >= limit:
                    break
                
                logger.info(f"🔍 Recherche WTTJ pour '{term}'...")
                term_jobs = await self.scrape_search_term(term, limit - len(jobs))
                jobs.extend(term_jobs)
                
                await asyncio.sleep(2)  # Politesse
            
            logger.info(f"✅ WTTJ: {len(jobs)} offres récupérées")
            return jobs[:limit]
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping WTTJ: {e}")
            return []
    
    async def scrape_search_term(self, term: str, limit: int) -> List[Dict[str, Any]]:
        """Scrape pour un terme de recherche spécifique"""
        jobs = []
        
        try:
            search_url = f"{self.search_url}?query={term}&page=1"
            html = await self.safe_request(search_url)
            soup = BeautifulSoup(html, 'html.parser')
            
            # WTTJ utilise des composants React, chercher les données JSON
            script_tags = soup.find_all('script', type='application/json')
            
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    # Chercher les offres dans la structure JSON
                    jobs_data = self.extract_jobs_from_json(data)
                    
                    for job_data in jobs_data[:limit]:
                        job = {
                            'title': job_data.get('name', ''),
                            'company': job_data.get('organization', {}).get('name', ''),
                            'location': job_data.get('location', ''),
                            'description': job_data.get('description', ''),
                            'url': f"{self.base_url}{job_data.get('slug', '')}",
                            'source': 'wttj',
                            'contract_type': job_data.get('contract_type', ''),
                            'published_at': job_data.get('published_at', '')
                        }
                        
                        if job['title'] and job['company']:
                            jobs.append(job)
                    
                    break  # Premier script JSON trouvé suffit
                    
                except json.JSONDecodeError:
                    continue
            
            # Fallback: scraping HTML classique si JSON non trouvé
            if not jobs:
                jobs = await self.fallback_html_scraping(soup, limit)
            
            return jobs
            
        except Exception as e:
            logger.error(f"Erreur scraping terme '{term}': {e}")
            return []
    
    def extract_jobs_from_json(self, data: dict) -> List[Dict]:
        """Extrait les offres depuis les données JSON de WTTJ"""
        jobs = []
        
        # Structure JSON de WTTJ peut varier, essayer différents chemins
        possible_paths = [
            ['props', 'pageProps', 'jobs'],
            ['props', 'initialState', 'jobs', 'items'],
            ['jobs'],
            ['data', 'jobs']
        ]
        
        for path in possible_paths:
            try:
                current = data
                for key in path:
                    current = current[key]
                
                if isinstance(current, list):
                    jobs = current
                    break
                    
            except (KeyError, TypeError):
                continue
        
        return jobs[:20]  # Limite raisonnable
    
    async def fallback_html_scraping(self, soup: BeautifulSoup, limit: int) -> List[Dict]:
        """Scraping HTML en fallback si JSON non disponible"""
        jobs = []
        
        # Sélecteurs CSS pour les éléments d'offres WTTJ
        job_cards = soup.select('.job-card, .offer-item, [data-testid="job-card"]')
        
        for card in job_cards[:limit]:
            try:
                title_elem = card.select_one('.job-title, .offer-title, h3, h4')
                company_elem = card.select_one('.company-name, .organization-name')
                location_elem = card.select_one('.location, .job-location')
                link_elem = card.select_one('a[href*="/jobs/"]')
                
                if title_elem and company_elem:
                    job = {
                        'title': title_elem.get_text(strip=True),
                        'company': company_elem.get_text(strip=True),
                        'location': location_elem.get_text(strip=True) if location_elem else '',
                        'description': '',  # Nécessiterait une requête supplémentaire
                        'url': f"{self.base_url}{link_elem.get('href')}" if link_elem else '',
                        'source': 'wttj'
                    }
                    jobs.append(job)
                    
            except Exception as e:
                logger.debug(f"Erreur parsing carte offre: {e}")
                continue
        
        return jobs
# scrapers/base_scraper.py - Classe de base pour les scrapers
import asyncio
import aiohttp
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from config import Config

class BaseScraper(ABC):
    """Classe de base pour tous les scrapers"""
    
    def __init__(self, name: str):
        self.name = name
        self.session = None
        self.headers = {
            'User-Agent': Config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def scrape_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Méthode principale de scraping à implémenter"""
        pass
    
    async def safe_request(self, url: str, delay: float = None) -> str:
        """Effectue une requête HTTP sécurisée avec rate limiting"""
        if delay is None:
            delay = Config.REQUEST_DELAY
        
        await asyncio.sleep(delay)
        
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.text()
            else:
                raise Exception(f"HTTP {response.status} pour {url}")
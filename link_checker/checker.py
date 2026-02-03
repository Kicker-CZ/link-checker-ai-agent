import aiohttp
import asyncio
from typing import Set, Dict, List, Optional
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class URLChecker:
    """Агент для проверки доступности ссылок на веб-странице."""
    
    def __init__(self, user_agent: str = None, timeout: int = 10):
        self.timeout = timeout
        self.headers = {'User-Agent': user_agent or 'LinkCheckerBot/1.0'}
        self.visited_urls: Set[str] = set()
        self.results: List[Dict] = []
        
    def get_all_links(self, url: str) -> Set[str]:
        """Извлекает все уникальные HTTP/HTTPS ссылки со страницы."""
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            links = set()
            for link in soup.find_all('a', href=True):
                href = link['href']
                absolute_url = urljoin(url, href)
                parsed = urlparse(absolute_url)
                
                # Берем только HTTP/HTTPS ссылки
                if parsed.scheme in ('http', 'https'):
                    links.add(absolute_url)
                    
            return links
        except Exception as e:
            logger.error(f"Ошибка при получении ссылок с {url}: {e}")
            return set()
    
    async def check_single_link(self, session: aiohttp.ClientSession, url: str) -> Dict:
        """Асинхронно проверяет доступность одной ссылки."""
        try:
            async with session.get(url, timeout=self.timeout) as response:
                return {
                    'url': url,
                    'status': response.status,
                    'reason': response.reason,
                    'ok': 200 <= response.status < 400,
                    'error': None
                }
        except Exception as e:
            return {
                'url': url,
                'status': None,
                'reason': str(e),
                'ok': False,
                'error': type(e).__name__
            }
    
    async def check_links(self, urls: Set[str], max_concurrent: int = 50) -> List[Dict]:
        """Асинхронно проверяет список ссылок с ограничением на количество одновременных запросов."""
        connector = aiohttp.TCPConnector(limit_per_host=10, limit=max_concurrent)
        async with aiohttp.ClientSession(headers=self.headers, connector=connector) as session:
            tasks = [self.check_single_link(session, url) for url in urls]
            results = await asyncio.gather(*tasks)
            return results
    
    def check(self, start_url: str, max_links: int = 1000) -> List[Dict]:
        """Основной метод: получает ссылки со страницы и проверяет их."""
        logger.info(f"Начинаю проверку страницы: {start_url}")
        
        # Шаг 1: Получить все ссылки со страницы
        links = self.get_all_links(start_url)
        logger.info(f"Найдено {len(links)} ссылок для проверки")
        
        # Ограничиваем количество, если нужно
        links_to_check = list(links)[:max_links]
        
        # Шаг 2: Асинхронная проверка всех ссылок
        asyncio.run(self.check_links(set(links_to_check)))
        
        # Шаг 3: Сортировка результатов
        self.results.sort(key=lambda x: (not x['ok'], x['url']))
        
        # Вывод статистики
        working = sum(1 for r in self.results if r['ok'])
        broken = len(self.results) - working
        logger.info(f"Проверка завершена. Рабочих: {working}, нерабочих: {broken}")
        
        return self.results

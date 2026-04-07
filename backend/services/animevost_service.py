"""AnimeVost parser — search, metadata, player embeds from v12.vost.pw."""

import logging
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote

logger = logging.getLogger(__name__)

ANIMEVOST_URL = 'https://v12.vost.pw'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}
TIMEOUT = 12


class AnimeVostService:
    def __init__(self, base_url=ANIMEVOST_URL):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def _get(self, url):
        try:
            r = self.session.get(url, timeout=TIMEOUT)
            r.raise_for_status()
            return BeautifulSoup(r.text, 'html.parser')
        except Exception as e:
            logger.exception('AnimeVost request failed: %s', url)
            return None

    def _abs_url(self, path):
        if not path or path.startswith('data:'):
            return None
        if path.startswith('http'):
            return path
        return urljoin(self.base_url + '/', path)

    def search(self, query, limit=20):
        """Search for anime on AnimeVost."""
        url = f'{self.base_url}/index.php?do=search&subaction=search&story={quote(query)}'
        soup = self._get(url)
        if not soup:
            return []

        results = []
        # AnimeVost uses .shortstory or similar containers for search results
        for item in soup.select('.shortstory, .shortimg')[:limit]:
            try:
                # Extract link
                link_el = item.select_one('a[href*="/tip/"]')
                if not link_el:
                    continue
                link = link_el.get('href', '')
                
                # Extract title
                title_el = item.select_one('.shortstoryHead a, h2 a, .zagolovok a')
                title = title_el.get_text(strip=True) if title_el else ''
                
                # Extract image
                img = item.select_one('img')
                img_src = self._abs_url(img.get('src')) if img else None
                
                # Extract ID from URL (e.g., /tip/tv/3856-title.html -> 3856)
                anime_id = ''
                match = re.search(r'/(\d+)-', link)
                if match:
                    anime_id = match.group(1)

                results.append({
                    'id': anime_id,
                    'title': title,
                    'url': self._abs_url(link),
                    'image': img_src,
                    'type': 'anime',
                })
            except Exception:
                continue

        return results

    def get_detail(self, url):
        """Get detailed info about an anime from its AnimeVost page URL."""
        soup = self._get(url)
        if not soup:
            return None

        result = {'url': url}

        # Title
        h1 = soup.select_one('h1, .zagolovok')
        result['title'] = h1.get_text(strip=True) if h1 else ''

        # Poster
        poster = soup.select_one('.imgRadius img, .postImg img')
        if poster:
            src = poster.get('src')
            result['poster'] = self._abs_url(src)
        else:
            og_image = soup.select_one('meta[property="og:image"], meta[name="twitter:image"]')
            result['poster'] = self._abs_url(og_image.get('content')) if og_image else None

        # Description
        desc_el = soup.select_one('.fullstory, .opisanie, [itemprop="description"]')
        result['description'] = desc_el.get_text(strip=True) if desc_el else ''

        # Extract metadata from info blocks
        result['info'] = {}
        result['year'] = None
        result['genres'] = []
        result['type'] = None
        result['episodes'] = None
        result['status'] = None

        # Parse info table or blocks
        for info_block in soup.select('.infoTable tr, .fullstory'):
            text = info_block.get_text()
            
            # Year
            year_match = re.search(r'Год.*?(\d{4})', text)
            if year_match:
                result['year'] = year_match.group(1)
            
            # Genres
            genre_match = re.search(r'Жанр.*?:(.*?)(?:\n|$)', text)
            if genre_match:
                genres_text = genre_match.group(1)
                result['genres'] = [g.strip() for g in re.split(r'[,،]', genres_text) if g.strip()]
            
            # Type
            type_match = re.search(r'Тип.*?:(.*?)(?:\n|$)', text)
            if type_match:
                result['type'] = type_match.group(1).strip()
            
            # Episodes
            ep_match = re.search(r'Серии.*?:.*?(\d+)', text)
            if ep_match:
                result['episodes'] = ep_match.group(1)
            
            # Status
            status_match = re.search(r'Статус.*?:(.*?)(?:\n|$)', text)
            if status_match:
                result['status'] = status_match.group(1).strip()

        # Extract anime ID from URL
        result['anime_id'] = None
        match = re.search(r'/(\d+)-', url)
        if match:
            result['anime_id'] = match.group(1)

        # Player embed URL — look for playerjs or iframe
        result['player_url'] = None
        
        # Check for playerjs initialization
        for script in soup.select('script'):
            script_text = script.get_text()
            # Look for playerjs file parameter
            file_match = re.search(r'file:\s*["\']([^"\']+)["\']', script_text)
            if file_match:
                result['player_url'] = file_match.group(1)
                break
        
        # Fallback: look for iframe
        if not result['player_url']:
            iframe = soup.select_one('iframe[src*="frame"], iframe[src*="player"]')
            if iframe:
                result['player_url'] = self._abs_url(iframe.get('src', ''))

        # Extract episode list if available
        result['episodes_list'] = []
        for ep_link in soup.select('.playlists-lists a, .playlists-items a'):
            ep_num = ep_link.get_text(strip=True)
            ep_data_id = ep_link.get('data-id', '')
            if ep_num:
                result['episodes_list'].append({
                    'episode': ep_num,
                    'data_id': ep_data_id,
                })

        result['source_url'] = url
        result['content_type'] = 'anime'

        return result

    def browse(self, page=1):
        """Browse latest anime releases."""
        url = f'{self.base_url}/'
        if page > 1:
            url += f'page/{page}/'
        
        soup = self._get(url)
        if not soup:
            return []

        results = []
        for item in soup.select('.shortstory, .shortimg'):
            try:
                link_el = item.select_one('a[href*="/tip/"]')
                if not link_el:
                    continue
                link = link_el.get('href', '')
                
                title_el = item.select_one('.shortstoryHead a, h2 a, .zagolovok a')
                title = title_el.get_text(strip=True) if title_el else ''
                
                img = item.select_one('img')
                img_src = self._abs_url(img.get('src')) if img else None
                
                anime_id = ''
                match = re.search(r'/(\d+)-', link)
                if match:
                    anime_id = match.group(1)

                results.append({
                    'id': anime_id,
                    'title': title,
                    'url': self._abs_url(link),
                    'image': img_src,
                })
            except Exception:
                continue

        return results

    def get_ongoing(self):
        """Get ongoing anime list."""
        url = f'{self.base_url}/ongoing/'
        soup = self._get(url)
        if not soup:
            return []

        results = []
        for item in soup.select('.shortstory, .shortimg'):
            try:
                link_el = item.select_one('a[href*="/tip/"]')
                if not link_el:
                    continue
                link = link_el.get('href', '')
                
                title_el = item.select_one('.shortstoryHead a, h2 a, .zagolovok a')
                title = title_el.get_text(strip=True) if title_el else ''
                
                img = item.select_one('img')
                img_src = self._abs_url(img.get('src')) if img else None
                
                anime_id = ''
                match = re.search(r'/(\d+)-', link)
                if match:
                    anime_id = match.group(1)

                results.append({
                    'id': anime_id,
                    'title': title,
                    'url': self._abs_url(link),
                    'image': img_src,
                    'status': 'ongoing',
                })
            except Exception:
                continue

        return results

    def get_genres(self):
        """Get list of anime genres."""
        return [
            {'id': 'boyevyye-iskusstva', 'name': 'Боевые искусства'},
            {'id': 'voyna', 'name': 'Война'},
            {'id': 'drama', 'name': 'Драма'},
            {'id': 'detektiv', 'name': 'Детектив'},
            {'id': 'istoriya', 'name': 'История'},
            {'id': 'komediya', 'name': 'Комедия'},
            {'id': 'mekha', 'name': 'Меха'},
            {'id': 'mistika', 'name': 'Мистика'},
            {'id': 'makho-sedze', 'name': 'Махо-сёдзё'},
            {'id': 'muzykalnyy', 'name': 'Музыкальный'},
            {'id': 'povsednevnost', 'name': 'Повседневность'},
            {'id': 'priklyucheniya', 'name': 'Приключения'},
            {'id': 'parodiya', 'name': 'Пародия'},
            {'id': 'romantika', 'name': 'Романтика'},
            {'id': 'senen', 'name': 'Сёнэн'},
            {'id': 'sedze', 'name': 'Сёдзё'},
            {'id': 'sport', 'name': 'Спорт'},
            {'id': 'skazka', 'name': 'Сказка'},
            {'id': 'sedze-ay', 'name': 'Сёдзё-ай'},
            {'id': 'senen-ay', 'name': 'Сёнэн-ай'},
            {'id': 'samurai', 'name': 'Самураи'},
            {'id': 'triller', 'name': 'Триллер'},
            {'id': 'uzhasy', 'name': 'Ужасы'},
            {'id': 'fantastika', 'name': 'Фантастика'},
            {'id': 'fentezi', 'name': 'Фэнтези'},
            {'id': 'shkola', 'name': 'Школа'},
            {'id': 'etti', 'name': 'Этти'},
        ]

    def browse_by_genre(self, genre_id, page=1):
        """Browse anime by genre."""
        url = f'{self.base_url}/zhanr/{genre_id}/'
        if page > 1:
            url += f'page/{page}/'
        
        soup = self._get(url)
        if not soup:
            return []

        results = []
        for item in soup.select('.shortstory, .shortimg'):
            try:
                link_el = item.select_one('a[href*="/tip/"]')
                if not link_el:
                    continue
                link = link_el.get('href', '')
                
                title_el = item.select_one('.shortstoryHead a, h2 a, .zagolovok a')
                title = title_el.get_text(strip=True) if title_el else ''
                
                img = item.select_one('img')
                img_src = self._abs_url(img.get('src')) if img else None
                
                anime_id = ''
                match = re.search(r'/(\d+)-', link)
                if match:
                    anime_id = match.group(1)

                results.append({
                    'id': anime_id,
                    'title': title,
                    'url': self._abs_url(link),
                    'image': img_src,
                })
            except Exception:
                continue

        return results


animevost_service = AnimeVostService()

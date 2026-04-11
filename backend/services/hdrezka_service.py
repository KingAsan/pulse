"""HDRezka mirror parser — search, metadata, player embeds, and direct streams from tv.hdrezka.inc."""

import logging
import re
import base64
import time
import requests
from itertools import product
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote

logger = logging.getLogger(__name__)

MIRROR_URL = 'https://tv.hdrezka.inc'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}
TIMEOUT = 12


class HdRezkaService:
    def __init__(self, base_url=MIRROR_URL):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def _get(self, url):
        try:
            r = self.session.get(url, timeout=TIMEOUT)
            r.raise_for_status()
            return BeautifulSoup(r.text, 'html.parser')
        except Exception as e:
            logger.exception('HdRezka request failed: %s', url)
            return None

    def _abs_url(self, path):
        if not path or path.startswith('data:'):
            return None
        if path.startswith('http'):
            return path
        return urljoin(self.base_url + '/', path)

    def search(self, query, limit=20):
        """Search for movies/series on HDRezka mirror."""
        url = f'{self.base_url}/search/?do=search&subaction=search&q={quote(query)}'
        soup = self._get(url)
        if not soup:
            return []

        results = []
        for item in soup.select('.postItem')[:limit]:
            try:
                data_id = item.get('data-id', '')
                cover = item.select_one('.postItem-cover')
                link = cover.get('data-link', '') if cover else ''
                img = item.select_one('img')
                img_src = self._abs_url(img.get('data-src') or img.get('src')) if img else None
                title_el = item.select_one('.postItem-title a, h3 a, a')
                title = title_el.get_text(strip=True) if title_el else ''

                # Determine type from URL
                content_type = 'movie'
                if '/serialy/' in link:
                    content_type = 'series'
                elif '/multfilmy/' in link or '/multserial/' in link:
                    content_type = 'cartoon'
                elif '/anime/' in link:
                    content_type = 'anime'

                results.append({
                    'id': data_id,
                    'title': title,
                    'url': link,
                    'image': img_src,
                    'type': content_type,
                })
            except Exception:
                continue

        return results

    def get_detail(self, url):
        """Get detailed info about a movie/series from its HDRezka page URL."""
        soup = self._get(url)
        if not soup:
            return None

        result = {'url': url}

        # Title
        h1 = soup.select_one('h1')
        result['title'] = h1.get_text(strip=True) if h1 else ''

        # Original title
        alt = soup.select_one('.altName')
        result['original_title'] = alt.get_text(strip=True) if alt else ''

        # Poster
        poster = soup.select_one('.posterBlock img, .postImg img')
        if poster:
            src = poster.get('data-src') or poster.get('src')
            result['poster'] = self._abs_url(src)
        else:
            result['poster'] = None

        # Info table
        table = soup.select_one('table.post__info')
        result['info'] = {}
        result['imdb_rating'] = None
        result['kp_rating'] = None
        result['year'] = None
        result['country'] = None
        result['genres'] = []
        result['quality'] = None
        result['duration'] = None
        result['translations'] = []

        if table:
            for row in table.select('tr'):
                label_el = row.select_one('td.l')
                value_el = row.select_one('td:not(.l)')
                if not label_el or not value_el:
                    continue
                label = label_el.get_text(strip=True).rstrip(':').lower()
                value = value_el.get_text(' ', strip=True)

                if 'рейтинг' in label:
                    imdb = value_el.select_one('.imdb .bold')
                    kp = value_el.select_one('.kp .bold')
                    if imdb:
                        try:
                            result['imdb_rating'] = float(imdb.get_text(strip=True))
                        except ValueError:
                            pass
                    if kp:
                        try:
                            result['kp_rating'] = float(kp.get_text(strip=True))
                        except ValueError:
                            pass
                elif 'дата выхода' in label or 'год' in label:
                    result['year'] = value.strip()
                elif 'страна' in label:
                    result['country'] = value.strip()
                elif 'жанр' in label:
                    result['genres'] = [g.strip() for g in value.split(',') if g.strip()]
                elif 'качеств' in label:
                    result['quality'] = value.strip()
                elif 'время' in label:
                    result['duration'] = value.strip()
                elif 'перевод' in label:
                    result['translations'] = [t.strip() for t in value.split(',') if t.strip()]

                result['info'][label] = value

        # Description
        desc_el = soup.select_one('.postDescription, .b-post__description_text, .story')
        result['description'] = desc_el.get_text(strip=True) if desc_el else ''

        # Extract post_id from page (data-id attribute or from init scripts)
        result['post_id'] = None
        # Try data-id on main content block
        content_block = soup.select_one('[data-id]')
        if content_block:
            result['post_id'] = content_block.get('data-id', '')

        # Try to extract from init scripts if not found
        if not result['post_id']:
            for script in soup.select('script'):
                text = script.get_text()
                match = re.search(r'(?:initCDNMoviesEvents|initCDNSeriesEvents)\(\s*(\d+)', text)
                if match:
                    result['post_id'] = match.group(1)
                    break
                match = re.search(r'sof\.tv\.(\d+)', text)
                if match:
                    result['post_id'] = match.group(1)
                    break

        # Extract translators (voice tracks)
        result['translator_list'] = []
        for li in soup.select('#translators-list li, .b-translators__list li'):
            tr_id = li.get('data-translator_id', '')
            title = li.get_text(strip=True)
            if tr_id:
                result['translator_list'].append({
                    'id': tr_id,
                    'title': title,
                })

        # If no translator list, try default from init script
        if not result['translator_list']:
            for script in soup.select('script'):
                text = script.get_text()
                match = re.search(r'(?:initCDNMoviesEvents|initCDNSeriesEvents)\(\s*\d+\s*,\s*(\d+)', text)
                if match:
                    result['translator_list'].append({
                        'id': match.group(1),
                        'title': 'По умолчанию',
                    })
                    break

        # Extract season/episode info for series from init scripts
        result['default_season'] = None
        result['default_episode'] = None
        for script in soup.select('script'):
            text = script.get_text()
            match = re.search(r'initCDNSeriesEvents\(\s*\d+\s*,\s*\d+\s*,\s*(\d+)\s*,\s*(\d+)', text)
            if match:
                result['default_season'] = match.group(1)
                result['default_episode'] = match.group(2)
                break

        # Player embed URL — check tabs first, then lazy iframes
        result['player_url'] = None
        for el in soup.select('.js-player-tabs li[data-src], .player-tabs li[data-src]'):
            src = el.get('data-src', '')
            if src and 'http' in src:
                result['player_url'] = src
                break
        if not result['player_url']:
            for iframe in soup.select('iframe[data-src], iframe[src]'):
                src = iframe.get('data-src') or iframe.get('src', '')
                if src and ('cinemar' in src or 'cinemap' in src or 'embed' in src):
                    result['player_url'] = src
                    break
        # Always provide the original page URL for "watch on site" fallback
        result['source_url'] = url

        # Related items
        related = []
        for rel in soup.select('.relatedItem, [data-id].relatedItem'):
            try:
                rel_id = rel.get('data-id', '')
                rel_link = rel.select_one('a')
                rel_title = rel.get_text(strip=True)[:100] if not rel_link else rel_link.get_text(strip=True)[:100]
                rel_href = rel_link.get('href', '') if rel_link else ''
                related.append({
                    'id': rel_id,
                    'title': rel_title,
                    'url': rel_href,
                })
            except Exception:
                continue
        result['related'] = related[:10]

        # Content type from URL
        result['content_type'] = 'movie'
        if '/serialy/' in url:
            result['content_type'] = 'series'
        elif '/multfilmy/' in url or '/multserial/' in url:
            result['content_type'] = 'cartoon'
        elif '/anime/' in url:
            result['content_type'] = 'anime'

        return result


    def get_seasons(self, url):
        """Extract list of seasons and episodes for a series from HDRezka page."""
        soup = self._get(url)
        if not soup:
            return []

        seasons = {}
        
        # Parse all initCDNSeriesEvents calls to get season/episode info
        for script in soup.select('script'):
            text = script.get_text()
            # Find all initCDNSeriesEvents calls
            matches = re.finditer(
                r'initCDNSeriesEvents\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)',
                text
            )
            for match in matches:
                post_id = match.group(1)
                translator_id = match.group(2)
                season = int(match.group(3))
                episode = int(match.group(4))
                
                if season not in seasons:
                    seasons[season] = []
                
                # Only add if not already present
                if not any(ep['episode'] == episode for ep in seasons[season]):
                    seasons[season].append({
                        'episode': episode,
                        'name': f'Эпизод {episode}',
                    })

        # Sort episodes within each season
        for season in seasons:
            seasons[season].sort(key=lambda x: x['episode'])

        # Convert to list format
        result = []
        for season_num in sorted(seasons.keys()):
            result.append({
                'season': season_num,
                'name': f'Сезон {season_num}',
                'episodes': seasons[season_num],
            })

        return result


    def get_categories(self):
        """Get main category pages from the site."""
        return [
            {'id': 'films', 'name': 'Фильмы', 'url': f'{self.base_url}/filmy/'},
            {'id': 'series', 'name': 'Сериалы', 'url': f'{self.base_url}/serialy/'},
            {'id': 'cartoons', 'name': 'Мультфильмы', 'url': f'{self.base_url}/multfilmy/'},
            {'id': 'anime', 'name': 'Аниме', 'url': f'{self.base_url}/anime/'},
        ]

    # ------------------------------------------------------------------
    # Stream extraction — parse cinemar.cc embed to get direct HLS URLs
    # ------------------------------------------------------------------

    def get_streams_from_embed(self, embed_url):
        """Extract HLS stream URLs from cinemar.cc embed page.

        Parses the Cinemar player config which contains base64-encoded JSON
        with voice tracks and their HLS playlist URLs.

        Returns list of voice tracks with HLS URLs.
        """
        if not embed_url:
            return []

        try:
            r = self.session.get(
                embed_url,
                headers={'Referer': f'{self.base_url}/'},
                timeout=15,
            )
            if r.status_code != 200:
                logger.warning('Embed fetch failed: %s -> %s', embed_url, r.status_code)
                return []

            html = r.text

            # Extract the "file" field from Cinemar player config
            match = re.search(r'"file":"(.*?)"', html)
            if not match:
                return []

            file_data = match.group(1).replace('\\/', '/')
            cleaned = file_data.lstrip('#')

            # Find base64 JSON start: W3s = [{ or eyJ = {"
            b64_start = -1
            for marker in ['W3s', 'eyJ']:
                idx = cleaned.find(marker)
                if idx >= 0:
                    b64_start = idx
                    break

            if b64_start < 0:
                return []

            b64_data = cleaned[b64_start:]
            # Clean non-base64 chars, strip existing padding
            b64_data = re.sub(r'[^A-Za-z0-9+/]', '', b64_data)
            # Truncate to valid base64 length (multiple of 4)
            b64_data = b64_data[:len(b64_data) - (len(b64_data) % 4)]

            decoded = base64.b64decode(b64_data).decode('utf-8', errors='replace')

            # Parse the JSON array — fix escape issues first
            # Find the closing bracket of the array
            bracket_count = 0
            end_idx = len(decoded)
            for i, c in enumerate(decoded):
                if c == '[':
                    bracket_count += 1
                elif c == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end_idx = i + 1
                        break

            json_str = decoded[:end_idx]
            # Fix invalid escape sequences that break json.loads
            json_str = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', json_str)

            import json as json_mod
            try:
                data = json_mod.loads(json_str, strict=False)
            except Exception:
                # Fallback to regex extraction
                data = []
                for m in re.finditer(
                    r'"voice_id":(\d+).*?"title":"((?:[^"\\]|\\.)*)".*?"file":"((?:[^"\\]|\\.)*)"',
                    decoded,
                ):
                    data.append({
                        'voice_id': int(m.group(1)),
                        'title': m.group(2),
                        'file': m.group(3).replace('\\/', '/'),
                    })

            tracks = []
            seen_voices = {}  # voice_id -> track (deduplicate)
            items = data if isinstance(data, list) else [data]
            for item in items:
                voice_id = str(item.get('voice_id', ''))
                title = item.get('title', '')
                file_url = item.get('file', '').replace('\\/', '/')

                # Strip HTML tags from title (e.g. <img src="flags/jp.png">)
                title = re.sub(r'<[^>]+>', '', title).strip()

                if not file_url or not title:
                    continue

                if file_url.startswith('//'):
                    file_url = 'https:' + file_url

                # Ensure master playlist URL (hls.m3u8) for quality selection
                has_quality = 'hls.m3u8' in file_url and 'hls-v' not in file_url

                # Deduplicate by voice_id — prefer tracks with quality
                if voice_id in seen_voices:
                    if has_quality and not seen_voices[voice_id]['has_quality']:
                        seen_voices[voice_id] = {
                            'voice_id': voice_id,
                            'title': title,
                            'hls_url': file_url,
                            'has_quality': has_quality,
                        }
                else:
                    seen_voices[voice_id] = {
                        'voice_id': voice_id,
                        'title': title,
                        'hls_url': file_url,
                        'has_quality': has_quality,
                    }

            return list(seen_voices.values())
        except Exception as e:
            logger.exception('get_streams_from_embed error: %s', embed_url)
            return []

    def browse(self, category='filmy', page=1):
        """Browse a category page."""
        url = f'{self.base_url}/{category}/'
        if page > 1:
            url += f'page/{page}/'
        soup = self._get(url)
        if not soup:
            return []

        results = []
        for item in soup.select('.postItem'):
            try:
                data_id = item.get('data-id', '')
                cover = item.select_one('.postItem-cover')
                link = cover.get('data-link', '') if cover else ''
                img = item.select_one('img')
                img_src = self._abs_url(img.get('data-src') or img.get('src')) if img else None
                title_el = item.select_one('.postItem-title a, h3 a, a')
                title = title_el.get_text(strip=True) if title_el else ''

                results.append({
                    'id': data_id,
                    'title': title,
                    'url': link,
                    'image': img_src,
                })
            except Exception:
                continue

        return results


hdrezka_service = HdRezkaService()

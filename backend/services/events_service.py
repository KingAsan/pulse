"""Events service — live parsing from kino.kz for entertainment events in Kazakhstan."""

import logging
import re
import json
import time
import requests

logger = logging.getLogger(__name__)

KINOKZ_BASE = 'https://kino.kz/ru'
CATEGORIES = {
    'concert': 'Концерты',
    'theatre': 'Театры',
    'standup': 'Стендап',
    'sport': 'Спорт',
    'art': 'Искусство',
    'entertainment': 'Развлечения',
    'family': 'Семейные',
    'tours': 'Туры',
}
CITIES = {
    '1': 'Астана',
    '2': 'Алматы',
}
TIMEOUT = 15
CACHE_TTL = 600  # 10 minutes


class KinoKzParser:
    """Parses event data from kino.kz RSC payloads."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'ru,en;q=0.9',
        })
        self._cache = {}  # key -> (data, timestamp)

    def _get_cached(self, key):
        if key in self._cache:
            data, ts = self._cache[key]
            if time.time() - ts < CACHE_TTL:
                return data
        return None

    def _set_cached(self, key, data):
        self._cache[key] = (data, time.time())

    def _extract_events_from_rsc(self, html):
        """Extract event objects from Next.js RSC payload in HTML."""
        seen_ids = set()
        events = []
        # Find all self.__next_f.push blocks
        for match in re.finditer(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html, re.DOTALL):
            raw = match.group(1)
            try:
                unescaped = raw.replace('\\"', '"').replace('\\n', '\n').replace('\\\\', '\\')
            except Exception:
                continue

            # Find event JSON objects by balanced brace matching
            for m in re.finditer(r'\{"id":\d+,', unescaped):
                text = unescaped[m.start():]
                depth = 0
                end = 0
                for i, c in enumerate(text):
                    if c == '{':
                        depth += 1
                    elif c == '}':
                        depth -= 1
                        if depth == 0:
                            end = i + 1
                            break
                if end == 0:
                    continue
                try:
                    obj = json.loads(text[:end])
                    # Must have next_session_date to be an event listing
                    if 'next_session_date' not in obj:
                        continue
                    eid = obj.get('id')
                    if eid in seen_ids:
                        continue
                    seen_ids.add(eid)
                    events.append(obj)
                except (json.JSONDecodeError, ValueError):
                    pass
        return events

    def _format_event(self, raw, category=None):
        """Convert raw kino.kz event object to our API format."""
        event_id = raw.get('id', '')
        name = raw.get('name') or raw.get('name_rus') or raw.get('name_origin', '')
        venue = raw.get('partner_name', '')
        city = raw.get('partner_city_name', '')
        poster = raw.get('small_poster', '')
        if not poster:
            posters = raw.get('posters', {})
            poster = posters.get('p344x489') or posters.get('p168x242', '')
        price_from = raw.get('price_from')
        price = f'от {price_from} ₸' if price_from else ''
        next_date = raw.get('next_session_date') or raw.get('premiere_kaz', '')
        event_type = raw.get('event_type_name', '')
        age = raw.get('age_restriction')
        age_label = f'{age}+' if age else ''

        return {
            'id': event_id,
            'title': name,
            'type': event_type or (CATEGORIES.get(category, '') if category else ''),
            'venue': venue,
            'city': city,
            'date': next_date,
            'time': '',
            'price': price,
            'image': poster,
            'age': age_label,
            'description': raw.get('presentation', '') or '',
            'genres': [],
            'source': 'kino.kz',
            'url': f'https://kino.kz/ru/{category}/event/{event_id}' if category else '',
        }

    def browse(self, city=None, event_type=None, category=None, limit=50):
        """Browse events, optionally filtered by city/type/category."""
        # If a specific category is requested, fetch only that
        categories_to_fetch = [category] if category else list(CATEGORIES.keys())

        # Determine city cookie
        city_id = '2'  # Default Almaty
        if city:
            city_lower = city.lower()
            if 'астана' in city_lower or 'astana' in city_lower:
                city_id = '1'
            elif 'алматы' in city_lower or 'almaty' in city_lower:
                city_id = '2'

        all_events = []
        for cat in categories_to_fetch:
            cache_key = f'browse:{cat}:{city_id}'
            cached = self._get_cached(cache_key)
            if cached is not None:
                all_events.extend(cached)
                continue

            url = f'{KINOKZ_BASE}/{cat}'
            try:
                r = self.session.get(
                    url,
                    cookies={'city': city_id},
                    timeout=TIMEOUT,
                )
                if r.status_code != 200:
                    logger.warning('kino.kz %s returned %s', cat, r.status_code)
                    continue

                raw_events = self._extract_events_from_rsc(r.text)
                formatted = [self._format_event(e, category=cat) for e in raw_events]
                # Deduplicate by id
                seen = set()
                unique = []
                for e in formatted:
                    if e['id'] not in seen:
                        seen.add(e['id'])
                        unique.append(e)
                self._set_cached(cache_key, unique)
                all_events.extend(unique)
            except Exception:
                logger.exception('Error fetching kino.kz category %s', cat)

        # Global dedup across categories (same event can appear in multiple categories)
        seen_global = set()
        deduped = []
        for e in all_events:
            eid = e['id']
            if eid not in seen_global:
                seen_global.add(eid)
                deduped.append(e)
        all_events = deduped

        # Apply filters
        if event_type:
            et = event_type.lower()
            all_events = [e for e in all_events if et in e.get('type', '').lower()]

        # Sort by date (soonest first)
        all_events.sort(key=lambda e: e.get('date') or '9999')

        return all_events[:limit]

    def search(self, query, city_id='2'):
        """Search events across all categories."""
        q = query.lower()
        # Fetch all categories and filter
        all_events = self.browse(limit=200)
        return [
            e for e in all_events
            if q in e['title'].lower()
            or q in e.get('venue', '').lower()
            or q in e.get('type', '').lower()
            or q in e.get('city', '').lower()
        ]

    def get_event(self, event_id, category=None):
        """Get event detail. Try cache first, then detail page."""
        # Search in cached browse data
        for key, (data, ts) in self._cache.items():
            if key.startswith('browse:') and time.time() - ts < CACHE_TTL:
                for e in data:
                    if str(e['id']) == str(event_id):
                        return e
        return None

    def get_types(self):
        """Return available event types."""
        return list(CATEGORIES.values())

    def get_cities(self):
        """Return available cities."""
        return list(CITIES.values())

    def get_categories(self):
        """Return category slugs and names for frontend tabs."""
        return [{'id': k, 'name': v} for k, v in CATEGORIES.items()]


events_service = KinoKzParser()

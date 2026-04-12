"""HDRezka routes — admin-only search, browse, detail, categories, streams via HdRezkaApi."""

import logging
import re
import hashlib
import time
import requests
from urllib.parse import quote, urljoin
from flask import Blueprint, request, jsonify, Response, current_app
from routes.admin import require_admin
from services.hdrezka_api_service import hdrezka_api_service
# Старый сервис оставлен для обратной совместимости (можно удалить позже)
# from services.hdrezka_service import hdrezka_service

logger = logging.getLogger(__name__)
hdrezka_bp = Blueprint('hdrezka', __name__)


def _sign_embed_url(url):
    """Create a short-lived HMAC token for an embed URL (valid 1 hour)."""
    ts = str(int(time.time()) // 3600)  # hour-granularity
    secret = current_app.config.get('SECRET_KEY', 'fallback')
    sig = hashlib.sha256(f'{secret}:{url}:{ts}'.encode()).hexdigest()[:24]
    return sig


def _verify_embed_sig(url, sig):
    """Verify embed signature (allows current + previous hour)."""
    secret = current_app.config.get('SECRET_KEY', 'fallback')
    now_h = int(time.time()) // 3600
    for h in (now_h, now_h - 1):
        expected = hashlib.sha256(f'{secret}:{url}:{h}'.encode()).hexdigest()[:24]
        if sig == expected:
            return True
    return False


@hdrezka_bp.route('/search')
@require_admin
def search():
    """Search HDRezka for movies/series."""
    q = request.args.get('q', '')
    if not q:
        return jsonify([])
    try:
        limit = request.args.get('limit', 20, type=int)
        return jsonify(hdrezka_api_service.search(q, limit=min(limit, 50)))
    except Exception as e:
        logger.exception('HDRezka search error: q=%s', q)
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@hdrezka_bp.route('/detail')
@require_admin
def detail():
    """Get detailed info about a movie/series from its HDRezka page URL."""
    url = request.args.get('url', '')
    if not url or not url.startswith('http'):
        return jsonify({'error': 'Valid url parameter required'}), 400
    try:
        result = hdrezka_api_service.get_detail(url)
        if not result:
            return jsonify({'error': 'Could not fetch details'}), 502
        # Sign the embed URL so the iframe proxy can verify without JWT
        if result.get('player_url'):
            result['embed_sig'] = _sign_embed_url(result['player_url'])
        return jsonify(result)
    except Exception as e:
        logger.exception('HDRezka detail error: url=%s', url)
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@hdrezka_bp.route('/browse')
@require_admin
def browse():
    """Browse a category page on HDRezka."""
    category = request.args.get('category', 'filmy')
    page = request.args.get('page', 1, type=int)
    try:
        return jsonify(hdrezka_api_service.browse(category=category, page=max(1, page)))
    except Exception as e:
        logger.exception('HDRezka browse error: cat=%s page=%s', category, page)
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@hdrezka_bp.route('/categories')
@require_admin
def categories():
    """Get list of HDRezka content categories."""
    try:
        return jsonify(hdrezka_api_service.get_categories())
    except Exception as e:
        logger.exception('HDRezka categories error')
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@hdrezka_bp.route('/seasons')
@require_admin
def seasons():
    """Get list of seasons and episodes for a series."""
    url = request.args.get('url', '')
    if not url or not url.startswith('http'):
        return jsonify({'error': 'Valid url parameter required'}), 400
    try:
        result = hdrezka_api_service.get_seasons(url)
        return jsonify({'seasons': result})
    except Exception as e:
        logger.exception('HDRezka seasons error: url=%s', url)
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@hdrezka_bp.route('/streams')
@require_admin
def streams():
    """Get voice tracks with direct video URLs from HDRezka.

    Optional parameters:
    - translator_id: voice track ID (for series with multiple translators)
    - season: season number (for series)
    - episode: episode number (for series)
    """
    url = request.args.get('url', '')
    translator_id = request.args.get('translator_id', '')
    season = request.args.get('season', '')
    episode = request.args.get('episode', '')

    if not url:
        return jsonify({'error': 'url parameter required'}), 400

    try:
        tracks = hdrezka_api_service.get_streams(url, season=season, episode=episode, translator_id=translator_id)
        if not tracks:
            return jsonify({'error': 'No streams found'}), 404

        # Добавить подписи для HLS проксирования
        for track in tracks:
            videos = track.get('videos', {})
            for quality, urls in videos.items():
                signed_urls = []
                for video_url in urls:
                    sig = _sign_embed_url(video_url)
                    signed_urls.append(f'/api/hdrezka/hls_proxy?url={quote(video_url)}&sig={sig}')
                videos[quality] = signed_urls

        return jsonify({'tracks': tracks})
    except Exception as e:
        logger.exception('HDRezka streams error')
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@hdrezka_bp.route('/hls_proxy')
def hls_proxy():
    """Proxy HLS video streams from HDRezka (CORS workaround).

    Authenticated via HMAC sig (same as embed proxy) since iframes/video
    elements can't send JWT headers.
    """
    url = request.args.get('url', '')
    sig = request.args.get('sig', '')
    if not url or not re.match(r'https?://', url):
        return Response('Invalid URL', status=400, content_type='text/plain')
    if not sig or not _verify_embed_sig(url, sig):
        return Response('Forbidden', status=403, content_type='text/plain')

    try:
        r = requests.get(url, timeout=20, stream=True)
        if r.status_code != 200:
            return Response(f'Upstream {r.status_code}', status=502)

        content_type = r.headers.get('Content-Type', 'application/octet-stream')

        # For m3u8 playlists, rewrite relative URLs to go through our proxy
        if 'mpegURL' in content_type or url.endswith('.m3u8'):
            text = r.text
            base_url = url.rsplit('/', 1)[0] + '/'
            lines = []
            for line in text.split('\n'):
                line_stripped = line.strip()
                if line_stripped and not line_stripped.startswith('#'):
                    # Resolve relative URL to absolute
                    abs_url = urljoin(url, line_stripped)
                    proxy_sig = _sign_embed_url(abs_url)
                    line = f'/api/hdrezka/hls_proxy?url={quote(abs_url)}&sig={proxy_sig}'
                lines.append(line)
            body = '\n'.join(lines)
            resp = Response(body, status=200, content_type='application/vnd.apple.mpegurl')
        else:
            # Binary segment (TS/MP4) — stream it through
            resp = Response(
                r.iter_content(chunk_size=65536),
                status=200,
                content_type=content_type,
            )

        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Cache-Control'] = 'public, max-age=300'
        return resp
    except Exception as e:
        logger.exception('HLS proxy error: url=%s', url[:80])
        return Response('Proxy error', status=503)


@hdrezka_bp.route('/embed')
def embed_proxy():
    """[DEPRECATED] Proxy HDRezka embed — now using direct streams via /streams endpoint."""
    return Response('This endpoint is deprecated. Use /streams instead.', status=410, content_type='text/plain')

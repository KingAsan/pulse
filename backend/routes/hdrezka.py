"""HDRezka routes — admin-only search, browse, detail, categories, embed proxy."""

import logging
import re
import hashlib
import time
from urllib.parse import quote, urljoin
from flask import Blueprint, request, jsonify, Response, current_app
from routes.admin import require_admin
from services.hdrezka_service import hdrezka_service

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
    """Search HDRezka mirror for movies/series."""
    q = request.args.get('q', '')
    if not q:
        return jsonify([])
    try:
        limit = request.args.get('limit', 20, type=int)
        return jsonify(hdrezka_service.search(q, limit=min(limit, 50)))
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
        result = hdrezka_service.get_detail(url)
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
    """Browse a category page on HDRezka mirror."""
    category = request.args.get('category', 'filmy')
    page = request.args.get('page', 1, type=int)
    try:
        return jsonify(hdrezka_service.browse(category=category, page=max(1, page)))
    except Exception as e:
        logger.exception('HDRezka browse error: cat=%s page=%s', category, page)
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@hdrezka_bp.route('/categories')
@require_admin
def categories():
    """Get list of HDRezka content categories."""
    try:
        return jsonify(hdrezka_service.get_categories())
    except Exception as e:
        logger.exception('HDRezka categories error')
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@hdrezka_bp.route('/streams')
@require_admin
def streams():
    """Get voice tracks with direct HLS URLs from cinemar.cc embed."""
    embed_url = request.args.get('embed_url', '')
    if not embed_url:
        return jsonify({'error': 'embed_url parameter required'}), 400

    try:
        tracks = hdrezka_service.get_streams_from_embed(embed_url)
        if not tracks:
            return jsonify({'error': 'No streams found'}), 404
        # Replace direct cinemap URLs with proxied URLs
        for track in tracks:
            hls_url = track.get('hls_url', '')
            if hls_url:
                sig = _sign_embed_url(hls_url)
                track['hls_url'] = f'/api/hdrezka/hls_proxy?url={quote(hls_url)}&sig={sig}'
        return jsonify({'tracks': tracks})
    except Exception as e:
        logger.exception('HDRezka streams error')
        return jsonify({'error': 'Service temporarily unavailable'}), 503


@hdrezka_bp.route('/hls_proxy')
def hls_proxy():
    """Proxy HLS playlists and segments from cinemap.cc (CORS workaround).

    Authenticated via HMAC sig (same as embed proxy) since iframes/video
    elements can't send JWT headers.
    """
    url = request.args.get('url', '')
    sig = request.args.get('sig', '')
    if not url or not re.match(r'https?://(v\d+\.)?(cinemar|cinemap)\.cc/', url):
        return Response('Invalid URL', status=400, content_type='text/plain')
    if not sig or not _verify_embed_sig(url, sig):
        return Response('Forbidden', status=403, content_type='text/plain')

    try:
        r = hdrezka_service.session.get(url, timeout=20, stream=True)
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
            # Binary segment (TS) — stream it through
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
    """Proxy cinemar.cc embed with correct Referer. Authenticated via HMAC sig, not JWT."""
    url = request.args.get('url', '')
    sig = request.args.get('sig', '')
    if not url or not re.match(r'https?://(cinemar|cinemap)\.cc/', url):
        return Response('Invalid embed URL', status=400, content_type='text/plain')
    if not sig or not _verify_embed_sig(url, sig):
        return Response('Forbidden', status=403, content_type='text/plain')
    try:
        r = hdrezka_service.session.get(
            url,
            headers={'Referer': 'https://tv.hdrezka.inc/'},
            timeout=15,
        )
        if r.status_code != 200:
            return Response(f'Upstream error: {r.status_code}', status=502, content_type='text/plain')

        html = r.text
        # Rewrite relative asset URLs to absolute so they load from cinemar.cc
        base_domain = re.match(r'(https?://[^/]+)', url).group(1)
        html = html.replace('href="/', f'href="{base_domain}/')
        html = html.replace("href='/", f"href='{base_domain}/")
        html = html.replace('src="/', f'src="{base_domain}/')
        html = html.replace("src='/", f"src='{base_domain}/")

        # Fix Cloudflare Rocket Loader: strip CF hash from script types
        # so scripts execute normally without the Rocket Loader dependency
        html = re.sub(r'type="[a-f0-9]+-text/javascript"', 'type="text/javascript"', html)
        # Remove Rocket Loader script itself (not needed, can break things)
        html = re.sub(r'<script[^>]*rocket-loader[^>]*></script>', '', html)

        # Inject JS patch: after Cinemar player decodes file data, replace
        # single-variant HLS URLs (hls-v1-a2.m3u8) with master playlist (hls.m3u8)
        # so the player can offer quality selection (240p-1080p)
        quality_patch = """<script type="text/javascript">
(function(){
  // === Strategy 1: Patch Hls.prototype.loadSource ===
  // hls.js uses its own loader (not fetch/XHR), so we intercept at the API level
  function patchHls() {
    if (typeof Hls !== 'undefined' && Hls.prototype && Hls.prototype.loadSource) {
      var origLoadSource = Hls.prototype.loadSource;
      Hls.prototype.loadSource = function(url) {
        if (typeof url === 'string' && /hls-v\\d+-a\\d+\\.m3u8/.test(url)) {
          console.log('[Pulse] Rewriting HLS URL for quality selection:', url);
          url = url.replace(/hls-v\\d+-a\\d+\\.m3u8/, 'hls.m3u8');
          console.log('[Pulse] New URL:', url);
        }
        return origLoadSource.call(this, url);
      };
      console.log('[Pulse] Hls.prototype.loadSource patched OK');
      return true;
    }
    return false;
  }

  // === Strategy 2: Intercept Hls constructor to patch config ===
  // If the player creates Hls with a custom loader, we also intercept the constructor
  if (typeof window.Hls !== 'undefined') {
    patchHls();
  }

  // === Strategy 3: Watch for Hls to appear (scripts load async) ===
  // Poll until Hls is defined, then patch it
  var attempts = 0;
  var patchInterval = setInterval(function() {
    attempts++;
    if (patchHls() || attempts > 100) {
      clearInterval(patchInterval);
    }
  }, 50);

  // === Strategy 4: Also patch fetch/XHR as fallback ===
  var origFetch = window.fetch;
  window.fetch = function(url, opts) {
    if (typeof url === 'string' && /hls-v\\d+-a\\d+\\.m3u8/.test(url)) {
      url = url.replace(/hls-v\\d+-a\\d+\\.m3u8/, 'hls.m3u8');
    }
    return origFetch.call(this, url, opts);
  };
  var origOpen = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function(method, url) {
    if (typeof url === 'string' && /hls-v\\d+-a\\d+\\.m3u8/.test(url)) {
      url = url.replace(/hls-v\\d+-a\\d+\\.m3u8/, 'hls.m3u8');
    }
    return origOpen.apply(this, [method, url].concat(Array.prototype.slice.call(arguments, 2)));
  };
})();
</script>"""
        html = html.replace('<body', quality_patch + '<body', 1)

        # Inject custom Pulse gradient theme CSS (uses actual cinemar player classes)
        pulse_css = """<style id="pulse-theme">
/* === Pulse Cinema Player Theme === */
:root{
  --pulse-bg:#0a0a14;
  --pulse-accent:#00d4ff;
  --pulse-purple:#7c3aed;
  --pulse-pink:#f472b6;
  --pulse-text:#e0e0ff;
  --pulse-muted:#a0a0c0;
  --scrollbar:#0a0a14;
  --scrollbar-thumb:#00d4ff;
  --scrollbar-thumb-hover:#7c3aed
}
body{background:var(--pulse-bg)!important;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif!important}

/* Playlist bar (season/episode/voice selectors) */
.playlist{gap:6px!important}
button.playlist-title{
  background:rgba(15,15,30,.9)!important;
  border:1px solid rgba(0,212,255,.25)!important;
  border-radius:10px!important;
  color:var(--pulse-text)!important;
  padding:8px 28px 8px 14px!important;
  font-size:13px!important;
  backdrop-filter:blur(8px)!important;
  transition:border-color .2s,background .2s!important
}
button.playlist-title:hover,
.playlist-group.is-open .playlist-title{
  background:rgba(0,212,255,.08)!important;
  border-color:var(--pulse-accent)!important;
  color:#fff!important
}

/* Dropdown menu */
.playlist-dropdown{
  background:rgba(12,12,24,.96)!important;
  border:1px solid rgba(0,212,255,.2)!important;
  border-radius:12px!important;
  border-top:none!important;
  border-bottom:none!important;
  backdrop-filter:blur(16px)!important;
  box-shadow:0 12px 40px rgba(0,0,0,.6),0 0 1px rgba(0,212,255,.3)!important;
  padding:4px 0!important;
  gap:0!important
}
.playlist-dropdown button{
  color:var(--pulse-muted)!important;
  padding:10px 30px 10px 14px!important;
  border-radius:8px!important;
  margin:1px 4px!important;
  transition:all .15s!important
}
.playlist-dropdown button:hover,
.playlist-dropdown button:focus{
  background:rgba(0,212,255,.1)!important;
  color:#fff!important
}
.playlist-dropdown button.is-active{
  background:linear-gradient(90deg,rgba(0,212,255,.18),rgba(124,58,237,.08))!important;
  color:var(--pulse-accent)!important
}

/* Download panel */
.download-window{
  background:rgba(12,12,24,.98)!important;
  backdrop-filter:blur(16px)!important
}
.download-header{
  color:var(--pulse-text)!important;
  border-bottom-color:rgba(0,212,255,.15)!important
}
.download-content button,
.download-content a{
  color:var(--pulse-muted)!important;
  border-radius:8px!important;
  transition:all .15s!important
}
.download-content button:hover,
.download-content a:hover{
  background:rgba(0,212,255,.1)!important;
  color:#fff!important
}

/* Alert/settings modal */
.alert-modal{
  background:rgba(15,15,30,.98)!important;
  border:1px solid rgba(0,212,255,.2)!important;
  border-radius:14px!important;
  backdrop-filter:blur(16px)!important;
  box-shadow:0 16px 48px rgba(0,0,0,.6)!important
}
.alert-text{color:var(--pulse-muted)!important}
.alert-footer{
  background:rgba(0,0,0,.15)!important;
  border-top-color:rgba(0,212,255,.1)!important
}
.alert-button{
  background:rgba(0,212,255,.12)!important;
  border:1px solid rgba(0,212,255,.3)!important;
  border-radius:8px!important;
  color:var(--pulse-text)!important;
  transition:all .2s!important
}
.alert-button:hover{
  background:rgba(0,212,255,.2)!important;
  border-color:var(--pulse-accent)!important
}

/* Continue watching button */
.continue{
  background:rgba(15,15,30,.9)!important;
  border:1px solid rgba(0,212,255,.25)!important;
  border-radius:10px!important;
  color:var(--pulse-text)!important;
  backdrop-filter:blur(8px)!important
}
.continue:hover{
  background:rgba(0,212,255,.12)!important;
  color:#fff!important
}

/* Scrollbar */
::-webkit-scrollbar{width:5px!important}
::-webkit-scrollbar-track{background:rgba(10,10,20,.3)!important}
::-webkit-scrollbar-thumb{
  background:linear-gradient(180deg,var(--pulse-accent),var(--pulse-purple))!important;
  border-radius:3px!important
}

/* Loading spinner */
.preload::before{
  border-color:rgba(0,212,255,.2)!important;
  border-top-color:var(--pulse-accent)!important
}
</style>"""

        # Inject before </head>
        html = html.replace('</head>', pulse_css + '</head>', 1)

        resp = Response(html, status=200, content_type='text/html; charset=utf-8')
        resp.headers['X-Frame-Options'] = 'SAMEORIGIN'
        return resp
    except Exception as e:
        logger.exception('HDRezka embed proxy error: url=%s', url)
        return Response('Proxy error', status=503, content_type='text/plain')

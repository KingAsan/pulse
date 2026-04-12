"""Simple CORS Proxy Server - runs alongside Flask to proxy HDRezka requests."""

from flask import Blueprint, request, Response
import requests as req
from urllib.parse import quote, unquote
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

logger = logging.getLogger(__name__)

# Create separate limiter for proxy (higher limits)
proxy_limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"],
    storage_uri="memory://",
)

cors_proxy_bp = Blueprint('cors_proxy', __name__)

# Session with proper headers
proxy_session = req.Session()
proxy_session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
})

@cors_proxy_bp.route('/api/proxy/hdrezka', methods=['GET', 'POST', 'OPTIONS'])
@proxy_limiter.limit("50 per minute")
def hdrezka_proxy():
    """Proxy requests to HDRezka through this endpoint.
    
    Query params:
    - url: Target URL (URL-encoded)
    - method: HTTP method (GET/POST)
    
    For POST requests, the body is forwarded as-is.
    """
    # Handle OPTIONS preflight
    if request.method == 'OPTIONS':
        resp = Response('', status=200)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return resp
    
    target_url = request.args.get('url', '')
    
    if not target_url:
        return Response('Missing url parameter', status=400, content_type='text/plain')
    
    # Only allow HDRezka URLs
    if 'hdrezka' not in target_url.lower():
        return Response('Only HDRezka URLs allowed', status=403, content_type='text/plain')
    
    try:
        # Prepare headers - forward some from original request
        headers = {
            'User-Agent': request.headers.get('User-Agent', proxy_session.headers['User-Agent']),
            'Referer': 'https://hdrezka.ag/',
        }
        
        # Forward content-type for POST requests
        if request.content_type and 'multipart' not in request.content_type:
            headers['Content-Type'] = request.content_type
        
        # Make the request based on method
        if request.method == 'POST':
            r = proxy_session.post(
                target_url,
                data=request.get_data(),
                headers=headers,
                timeout=20,
                stream=True,
            )
        else:
            r = proxy_session.get(
                target_url,
                headers=headers,
                timeout=20,
                stream=True,
            )
        
        # Handle compressed responses
        content = r.content
        
        # Create response with proper CORS headers
        resp = Response(
            content,
            status=r.status_code,
            content_type=r.headers.get('Content-Type', 'application/octet-stream'),
        )
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Cache-Control'] = 'public, max-age=300'
        
        # Forward encoding headers
        if 'Content-Encoding' in r.headers:
            resp.headers['Content-Encoding'] = r.headers['Content-Encoding']
        
        return resp
        
    except req.exceptions.Timeout:
        return Response('Proxy timeout', status=504, content_type='text/plain')
    except Exception as e:
        logger.exception('Proxy error')
        return Response(f'Proxy error: {str(e)}', status=502, content_type='text/plain')


@cors_proxy_bp.route('/api/proxy/health', methods=['GET'])
def proxy_health():
    """Health check for proxy."""
    return {'status': 'ok', 'proxy': 'hdrezka'}

"""Tests for AniLibria API routes."""

import pytest
import json


def test_anilibria_search(client, auth_header):
    """Test AniLibria search endpoint."""
    resp = client.get('/api/anilibria/search?q=Наруто', headers=auth_header)
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)


def test_anilibria_search_no_query(client, auth_header):
    """Test AniLibria search with no query returns empty."""
    resp = client.get('/api/anilibria/search', headers=auth_header)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == []


def test_anilibria_search_unauthorized(client):
    """Test AniLibria search requires auth."""
    resp = client.get('/api/anilibria/search?q=test')
    assert resp.status_code == 401


def test_anilibria_browse(client, auth_header):
    """Test AniLibria browse endpoint."""
    resp = client.get('/api/anilibria/browse', headers=auth_header)
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)


def test_anilibria_browse_with_page(client, auth_header):
    """Test AniLibria browse with pagination."""
    resp = client.get('/api/anilibria/browse?page=1&limit=10', headers=auth_header)
    assert resp.status_code == 200


def test_anilibria_ongoing(client, auth_header):
    """Test AniLibria ongoing endpoint."""
    resp = client.get('/api/anilibria/ongoing', headers=auth_header)
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)


def test_anilibria_genres(client, auth_header):
    """Test AniLibria genres endpoint."""
    resp = client.get('/api/anilibria/genres', headers=auth_header)
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_anilibria_browse_by_genre(client, auth_header):
    """Test AniLibria browse by genre."""
    resp = client.get('/api/anilibria/genre/action', headers=auth_header)
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)


def test_anilibria_detail_no_code(client, auth_header):
    """Test AniLibria detail requires code or id."""
    resp = client.get('/api/anilibria/detail', headers=auth_header)
    assert resp.status_code == 400


def test_anilibria_detail_by_code(client, auth_header):
    """Test AniLibria detail by code."""
    # This may return 502 if the code doesn't exist, but endpoint should exist
    resp = client.get('/api/anilibria/detail?code=test', headers=auth_header)
    assert resp.status_code in [200, 502]


def test_anilibria_detail_unauthorized(client):
    """Test AniLibria detail requires auth."""
    resp = client.get('/api/anilibria/detail?code=test')
    assert resp.status_code == 401


def test_anilibria_browse_unauthorized(client):
    """Test AniLibria browse requires auth."""
    resp = client.get('/api/anilibria/browse')
    assert resp.status_code == 401


def test_anilibria_ongoing_unauthorized(client):
    """Test AniLibria ongoing requires auth."""
    resp = client.get('/api/anilibria/ongoing')
    assert resp.status_code == 401


def test_anilibria_genres_unauthorized(client):
    """Test AniLibria genres requires auth."""
    resp = client.get('/api/anilibria/genres')
    assert resp.status_code == 401


def test_anilibria_browse_by_genre_unauthorized(client):
    """Test AniLibria genre browse requires auth."""
    resp = client.get('/api/anilibria/genre/action')
    assert resp.status_code == 401


def test_anilibria_schedule(client, auth_header):
    """Test AniLibria schedule endpoint."""
    resp = client.get('/api/anilibria/schedule', headers=auth_header)
    assert resp.status_code == 200


def test_anilibria_random(client, auth_header):
    """Test AniLibria random endpoint."""
    resp = client.get('/api/anilibria/random', headers=auth_header)
    assert resp.status_code == 200

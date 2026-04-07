"""Tests for AnimeVost routes."""

import pytest


def test_animevost_search(client, admin_header):
    """Test AnimeVost search endpoint."""
    resp = client.get('/api/animevost/search?q=naruto', headers=admin_header)
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)


def test_animevost_search_no_query(client, admin_header):
    """Test AnimeVost search without query returns empty list."""
    resp = client.get('/api/animevost/search', headers=admin_header)
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_animevost_search_unauthorized(client):
    """Test AnimeVost search requires admin."""
    resp = client.get('/api/animevost/search?q=naruto')
    assert resp.status_code == 401


def test_animevost_browse(client, admin_header):
    """Test AnimeVost browse endpoint."""
    resp = client.get('/api/animevost/browse', headers=admin_header)
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)


def test_animevost_browse_with_page(client, admin_header):
    """Test AnimeVost browse with pagination."""
    resp = client.get('/api/animevost/browse?page=2', headers=admin_header)
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)


def test_animevost_ongoing(client, admin_header):
    """Test AnimeVost ongoing endpoint."""
    resp = client.get('/api/animevost/ongoing', headers=admin_header)
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)


def test_animevost_genres(client, admin_header):
    """Test AnimeVost genres endpoint."""
    resp = client.get('/api/animevost/genres', headers=admin_header)
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) > 0
    # Check genre structure
    if data:
        genre = data[0]
        assert 'id' in genre
        assert 'name' in genre


def test_animevost_browse_by_genre(client, admin_header):
    """Test AnimeVost browse by genre."""
    resp = client.get('/api/animevost/genre/komediya', headers=admin_header)
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)


def test_animevost_detail_no_url(client, admin_header):
    """Test AnimeVost detail without URL returns error."""
    resp = client.get('/api/animevost/detail', headers=admin_header)
    assert resp.status_code == 400
    data = resp.get_json()
    assert 'error' in data


def test_animevost_detail_invalid_url(client, admin_header):
    """Test AnimeVost detail with invalid URL returns error."""
    resp = client.get('/api/animevost/detail?url=invalid', headers=admin_header)
    assert resp.status_code == 400
    data = resp.get_json()
    assert 'error' in data


def test_animevost_detail_unauthorized(client):
    """Test AnimeVost detail requires admin."""
    resp = client.get('/api/animevost/detail?url=https://v12.vost.pw/tip/tv/123-test.html')
    assert resp.status_code == 401


def test_animevost_browse_unauthorized(client):
    """Test AnimeVost browse requires admin."""
    resp = client.get('/api/animevost/browse')
    assert resp.status_code == 401


def test_animevost_ongoing_unauthorized(client):
    """Test AnimeVost ongoing requires admin."""
    resp = client.get('/api/animevost/ongoing')
    assert resp.status_code == 401


def test_animevost_genres_unauthorized(client):
    """Test AnimeVost genres requires admin."""
    resp = client.get('/api/animevost/genres')
    assert resp.status_code == 401


def test_animevost_browse_by_genre_unauthorized(client):
    """Test AnimeVost browse by genre requires admin."""
    resp = client.get('/api/animevost/genre/komediya')
    assert resp.status_code == 401

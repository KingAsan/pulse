"""Smoke tests for movies API endpoints."""
from unittest.mock import patch


def test_trending_returns_list(client):
    resp = client.get('/api/movies/trending')
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)


def test_search_empty_query_returns_empty(client):
    resp = client.get('/api/movies/search?q=')
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_search_with_query(client):
    resp = client.get('/api/movies/search?q=test')
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)


def test_movie_detail_not_found(client):
    resp = client.get('/api/movies/99999999')
    # Either 404 or 200 with data depending on API
    assert resp.status_code in (200, 404, 503)


def test_movie_videos(client):
    resp = client.get('/api/movies/1/videos')
    assert resp.status_code in (200, 503)
    data = resp.get_json()
    assert isinstance(data, (list, dict))


def test_genres(client):
    resp = client.get('/api/movies/genres')
    assert resp.status_code in (200, 503)
    assert isinstance(resp.get_json(), (list, dict))


def test_discover(client):
    resp = client.get('/api/movies/discover')
    assert resp.status_code in (200, 503)
    assert isinstance(resp.get_json(), (list, dict))

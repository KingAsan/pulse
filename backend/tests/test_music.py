"""Smoke tests for music API endpoints."""


def test_chart_returns_list(client):
    resp = client.get('/api/music/chart')
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)


def test_chart_with_limit(client):
    resp = client.get('/api/music/chart?limit=10')
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)


def test_search_empty_returns_empty(client):
    resp = client.get('/api/music/search?q=')
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_search_with_query(client):
    resp = client.get('/api/music/search?q=rock')
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)


def test_genres(client):
    resp = client.get('/api/music/genres')
    assert resp.status_code in (200, 503)
    assert isinstance(resp.get_json(), (list, dict))


def test_track_not_found(client):
    resp = client.get('/api/music/track/0')
    assert resp.status_code in (200, 404, 503)

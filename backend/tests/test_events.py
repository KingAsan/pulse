"""Smoke tests for events API endpoints."""


def test_browse_returns_list(client):
    resp = client.get('/api/events/browse')
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)


def test_browse_with_city(client):
    resp = client.get('/api/events/browse?city=Astana')
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)


def test_search_empty_returns_empty(client):
    resp = client.get('/api/events/search?q=')
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_search_with_query(client):
    resp = client.get('/api/events/search?q=concert')
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)


def test_event_not_found(client):
    resp = client.get('/api/events/99999')
    assert resp.status_code in (200, 404)


def test_types(client):
    resp = client.get('/api/events/types')
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)


def test_cities(client):
    resp = client.get('/api/events/cities')
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)

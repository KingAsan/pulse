"""Smoke tests for books API endpoints."""


def test_trending_returns_list(client):
    resp = client.get('/api/books/trending')
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)


def test_search_empty_returns_empty(client):
    resp = client.get('/api/books/search?q=')
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_search_with_query(client):
    resp = client.get('/api/books/search?q=python')
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)


def test_book_detail_not_found(client):
    resp = client.get('/api/books/detail/nonexistent-id-12345')
    assert resp.status_code in (200, 404, 503)


def test_subjects(client):
    resp = client.get('/api/books/subjects/fiction')
    assert resp.status_code in (200, 503)
    assert isinstance(resp.get_json(), (list, dict))

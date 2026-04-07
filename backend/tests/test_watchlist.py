"""Tests for watchlist and search history endpoints."""


def test_add_to_watchlist(client, auth_header):
    resp = client.post('/api/profile/watchlist', json={
        'item_type': 'movie', 'item_id': 'w1', 'title': 'Watch Later'
    }, headers=auth_header)
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'added'


def test_get_watchlist(client, auth_header):
    client.post('/api/profile/watchlist', json={
        'item_type': 'movie', 'item_id': 'w2', 'title': 'Movie 2'
    }, headers=auth_header)
    resp = client.get('/api/profile/watchlist', headers=auth_header)
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)
    assert len(resp.get_json()) >= 1


def test_check_watchlist(client, auth_header):
    client.post('/api/profile/watchlist', json={
        'item_type': 'book', 'item_id': 'wc1', 'title': 'Book'
    }, headers=auth_header)
    resp = client.get('/api/profile/watchlist/check?item_type=book&item_id=wc1', headers=auth_header)
    assert resp.status_code == 200
    assert resp.get_json()['in_watchlist'] is True


def test_remove_from_watchlist(client, auth_header):
    client.post('/api/profile/watchlist', json={
        'item_type': 'movie', 'item_id': 'wr1', 'title': 'Remove Me'
    }, headers=auth_header)
    resp = client.delete('/api/profile/watchlist', json={
        'item_type': 'movie', 'item_id': 'wr1'
    }, headers=auth_header)
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'removed'


def test_add_search_history(client, auth_header):
    resp = client.post('/api/profile/search-history', json={
        'query': 'test search', 'category': 'movie'
    }, headers=auth_header)
    assert resp.status_code == 200


def test_get_search_history(client, auth_header):
    client.post('/api/profile/search-history', json={
        'query': 'another search', 'category': 'book'
    }, headers=auth_header)
    resp = client.get('/api/profile/search-history', headers=auth_header)
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)


def test_check_favorite(client, auth_header):
    resp = client.get('/api/profile/favorites/check?item_type=movie&item_id=nonexistent', headers=auth_header)
    assert resp.status_code == 200
    assert resp.get_json()['is_favorite'] is False


def test_check_rating(client, auth_header):
    resp = client.get('/api/profile/ratings/check?item_type=movie&item_id=nonexistent', headers=auth_header)
    assert resp.status_code == 200
    assert resp.get_json()['rating'] == 0

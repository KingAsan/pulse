def test_add_favorite(client, auth_header):
    resp = client.post('/api/profile/favorites', json={
        'item_type': 'movie', 'item_id': 'tt123', 'title': 'Test Movie'
    }, headers=auth_header)
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'added'


def test_get_favorites(client, auth_header):
    client.post('/api/profile/favorites', json={
        'item_type': 'movie', 'item_id': 'tt456', 'title': 'Movie 2'
    }, headers=auth_header)
    resp = client.get('/api/profile/favorites', headers=auth_header)
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) >= 1


def test_remove_favorite(client, auth_header):
    client.post('/api/profile/favorites', json={
        'item_type': 'book', 'item_id': 'b1', 'title': 'Test Book'
    }, headers=auth_header)
    resp = client.delete('/api/profile/favorites', json={
        'item_type': 'book', 'item_id': 'b1'
    }, headers=auth_header)
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'removed'


def test_add_rating(client, auth_header):
    resp = client.post('/api/profile/ratings', json={
        'item_type': 'movie', 'item_id': 'tt789', 'rating': 4
    }, headers=auth_header)
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'rated'


def test_get_stats(client, auth_header):
    resp = client.get('/api/profile/stats', headers=auth_header)
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'favorites' in data
    assert 'ratings' in data


def test_export_user_data(client, auth_header):
    resp = client.get('/api/profile/export', headers=auth_header)
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'profile' in data
    assert 'favorites' in data
    assert 'export_date' in data

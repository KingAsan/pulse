"""Tests for recommendations and AI chat endpoints."""


def test_for_you_requires_auth(client):
    resp = client.get('/api/recommendations/for-you')
    assert resp.status_code == 401


def test_for_you_authenticated(client, auth_header):
    resp = client.get('/api/recommendations/for-you', headers=auth_header)
    assert resp.status_code in (200, 503)


def test_taste_requires_auth(client):
    resp = client.get('/api/recommendations/taste')
    assert resp.status_code == 401


def test_taste_authenticated(client, auth_header):
    resp = client.get('/api/recommendations/taste', headers=auth_header)
    assert resp.status_code in (200, 503)


def test_because_you_liked_requires_auth(client):
    resp = client.get('/api/recommendations/because-you-liked/movie/1')
    assert resp.status_code == 401


def test_ai_sessions_requires_auth(client):
    resp = client.get('/api/ai/sessions')
    assert resp.status_code == 401


def test_ai_sessions_authenticated(client, auth_header):
    resp = client.get('/api/ai/sessions', headers=auth_header)
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)


def test_ai_feedback_validation(client, auth_header):
    resp = client.post('/api/ai/feedback', json={
        'feedback_type': 'invalid', 'title': 'Test'
    }, headers=auth_header)
    assert resp.status_code == 400


def test_ai_feedback_missing_title(client, auth_header):
    resp = client.post('/api/ai/feedback', json={
        'feedback_type': 'like', 'title': ''
    }, headers=auth_header)
    assert resp.status_code == 400


def test_ai_feedback_success(client, auth_header):
    resp = client.post('/api/ai/feedback', json={
        'feedback_type': 'like', 'title': 'Test Movie', 'session_id': 's1'
    }, headers=auth_header)
    assert resp.status_code == 200


def test_ai_preferences_get(client, auth_header):
    resp = client.get('/api/ai/preferences', headers=auth_header)
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'favorite_categories' in data


def test_ai_onboarding_status(client, auth_header):
    resp = client.get('/api/ai/onboarding/status', headers=auth_header)
    assert resp.status_code == 200
    assert 'completed' in resp.get_json()


def test_ai_insights(client, auth_header):
    resp = client.get('/api/ai/insights', headers=auth_header)
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'total_queries' in data
    assert 'daily_limit' in data


def test_health(client):
    resp = client.get('/api/health')
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'ok'

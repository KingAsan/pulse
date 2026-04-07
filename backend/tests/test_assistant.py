def test_log_activity(client, auth_header):
    resp = client.post('/api/assistant/activity', json={
        'title': 'Test Movie', 'item_type': 'movie', 'item_id': 'tt1', 'action': 'watched'
    }, headers=auth_header)
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'logged'


def test_get_activity(client, auth_header):
    client.post('/api/assistant/activity', json={
        'title': 'Activity Test', 'item_type': 'book', 'item_id': 'b1', 'action': 'read'
    }, headers=auth_header)
    resp = client.get('/api/assistant/activity', headers=auth_header)
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_weekly_recap(client, auth_header):
    resp = client.get('/api/assistant/weekly-recap', headers=auth_header)
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'total_consumed' in data
    assert 'trend' in data


def test_notifications(client, auth_header):
    # Logging activity creates a notification
    client.post('/api/assistant/activity', json={
        'title': 'Notif Movie', 'item_type': 'movie', 'item_id': 'n1', 'action': 'watched'
    }, headers=auth_header)
    resp = client.get('/api/assistant/notifications', headers=auth_header)
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'notifications' in data
    assert 'unread' in data


def test_mark_notifications_read(client, auth_header):
    client.post('/api/assistant/activity', json={
        'title': 'Read Test', 'item_type': 'movie', 'item_id': 'r1', 'action': 'watched'
    }, headers=auth_header)
    resp = client.put('/api/assistant/notifications/read', json={}, headers=auth_header)
    assert resp.status_code == 200

    notifs = client.get('/api/assistant/notifications', headers=auth_header).get_json()
    assert notifs['unread'] == 0


def test_create_reminder(client, auth_header):
    resp = client.post('/api/assistant/reminders', json={
        'title': 'Watch later', 'item_type': 'movie', 'item_id': 'rem1',
        'remind_at': '2026-12-31T18:00:00'
    }, headers=auth_header)
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'created'


def test_get_reminders(client, auth_header):
    client.post('/api/assistant/reminders', json={
        'title': 'Reminder Test', 'item_type': 'book', 'item_id': 'rem2',
        'remind_at': '2026-12-31T20:00:00'
    }, headers=auth_header)
    resp = client.get('/api/assistant/reminders', headers=auth_header)
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)


def test_summary(client, auth_header):
    resp = client.get('/api/assistant/summary', headers=auth_header)
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'total_consumed' in data
    assert 'streak' in data

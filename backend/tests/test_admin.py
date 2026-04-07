def test_admin_stats_requires_admin(client, second_user_header):
    resp = client.get('/api/admin/stats', headers=second_user_header)
    assert resp.status_code == 403


def test_admin_stats_success(client, admin_header):
    resp = client.get('/api/admin/stats', headers=admin_header)
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'users_total' in data


def test_admin_list_users(client, admin_header):
    resp = client.get('/api/admin/users', headers=admin_header)
    assert resp.status_code == 200
    users = resp.get_json()
    assert len(users) >= 1


def test_admin_block_user(client, admin_header, second_user_header):
    users = client.get('/api/admin/users', headers=admin_header).get_json()
    non_admin = [u for u in users if not u['is_admin']][0]
    resp = client.put(f'/api/admin/users/{non_admin["id"]}', json={
        'is_blocked': True
    }, headers=admin_header)
    assert resp.status_code == 200


def test_admin_audit_log(client, admin_header, second_user_header):
    # Perform an admin action first
    users = client.get('/api/admin/users', headers=admin_header).get_json()
    non_admin = [u for u in users if not u['is_admin']][0]
    client.put(f'/api/admin/users/{non_admin["id"]}', json={'is_blocked': True}, headers=admin_header)

    resp = client.get('/api/admin/audit-log', headers=admin_header)
    assert resp.status_code == 200
    logs = resp.get_json()
    assert len(logs) >= 1
    assert logs[0]['action'] == 'update_user'

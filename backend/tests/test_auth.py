def test_register_success(client):
    resp = client.post('/api/auth/register', json={
        'username': 'newuser', 'email': 'new@example.com', 'password': 'StrongPass1'
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert 'token' in data
    assert data['user']['username'] == 'newuser'


def test_register_weak_password(client):
    resp = client.post('/api/auth/register', json={
        'username': 'weakuser', 'email': 'weak@example.com', 'password': '123'
    })
    assert resp.status_code == 400
    assert 'at least 8' in resp.get_json()['error']


def test_register_no_uppercase(client):
    resp = client.post('/api/auth/register', json={
        'username': 'noup', 'email': 'noup@example.com', 'password': 'alllower1'
    })
    assert resp.status_code == 400
    assert 'uppercase' in resp.get_json()['error']


def test_register_no_digit(client):
    resp = client.post('/api/auth/register', json={
        'username': 'nodig', 'email': 'nodig@example.com', 'password': 'AllLetters'
    })
    assert resp.status_code == 400
    assert 'digit' in resp.get_json()['error']


def test_register_invalid_email(client):
    resp = client.post('/api/auth/register', json={
        'username': 'bademail', 'email': 'notanemail', 'password': 'StrongPass1'
    })
    assert resp.status_code == 400
    assert 'email' in resp.get_json()['error'].lower()


def test_register_duplicate(client):
    client.post('/api/auth/register', json={
        'username': 'dup', 'email': 'dup@example.com', 'password': 'StrongPass1'
    })
    resp = client.post('/api/auth/register', json={
        'username': 'dup', 'email': 'dup2@example.com', 'password': 'StrongPass1'
    })
    assert resp.status_code == 409


def test_login_success(client):
    client.post('/api/auth/register', json={
        'username': 'loginuser', 'email': 'login@example.com', 'password': 'StrongPass1'
    })
    resp = client.post('/api/auth/login', json={
        'username': 'loginuser', 'password': 'StrongPass1'
    })
    assert resp.status_code == 200
    assert 'token' in resp.get_json()


def test_login_wrong_password(client):
    client.post('/api/auth/register', json={
        'username': 'wrongpw', 'email': 'wrong@example.com', 'password': 'StrongPass1'
    })
    resp = client.post('/api/auth/login', json={
        'username': 'wrongpw', 'password': 'WrongPassword1'
    })
    assert resp.status_code == 401


def test_me_endpoint(client, auth_header):
    resp = client.get('/api/auth/me', headers=auth_header)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['username'] == 'testuser'


def test_me_without_auth(client):
    resp = client.get('/api/auth/me')
    assert resp.status_code == 401


def test_first_user_is_admin(client):
    resp = client.post('/api/auth/register', json={
        'username': 'firstadmin', 'email': 'first@example.com', 'password': 'StrongPass1'
    })
    data = resp.get_json()
    assert data['user']['is_admin'] is True

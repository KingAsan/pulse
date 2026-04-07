import os
import sys
import tempfile
import pytest

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set test environment variables before importing anything
os.environ['SECRET_KEY'] = 'test-secret-key-minimum-32-chars-long!'
os.environ['JWT_SECRET_KEY'] = 'test-jwt-secret-key-min-32-chars-ok!'


@pytest.fixture
def app(tmp_path):
    import database
    from app import create_app

    db_file = str(tmp_path / 'test.db')
    database.DB_PATH = db_file

    app = create_app()
    app.config['TESTING'] = True
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_header(client):
    """Register a test user and return auth header."""
    resp = client.post('/api/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'TestPass1'
    })
    token = resp.get_json()['token']
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def admin_header(client):
    """Register the first user (becomes admin) and return auth header."""
    resp = client.post('/api/auth/register', json={
        'username': 'admin',
        'email': 'admin@example.com',
        'password': 'AdminPass1'
    })
    token = resp.get_json()['token']
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def second_user_header(client, admin_header):
    """Register a second (non-admin) user."""
    resp = client.post('/api/auth/register', json={
        'username': 'user2',
        'email': 'user2@example.com',
        'password': 'UserPass2'
    })
    token = resp.get_json()['token']
    return {'Authorization': f'Bearer {token}'}

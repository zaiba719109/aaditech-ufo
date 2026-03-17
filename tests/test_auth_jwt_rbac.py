"""Integration tests for JWT auth endpoints and RBAC enforcement."""

import uuid

from server.auth import get_api_key
from server.auth import hash_password
from server.extensions import db
from server.models import Organization, User, Role, Permission


def _api_key_headers(extra=None):
    headers = {'X-API-Key': get_api_key()}
    if extra:
        headers.update(extra)
    return headers


def _register_user(client, email=None):
    if email is None:
        email = f"owner-{uuid.uuid4().hex[:8]}@tenant.local"

    response = client.post(
        '/api/auth/register',
        headers=_api_key_headers(),
        json={
            'email': email,
            'full_name': 'Tenant Owner',
            'password': 'StrongPass123',
        },
    )
    assert response.status_code == 201
    return email


def _login_user(client, email):
    response = client.post(
        '/api/auth/login',
        json={'email': email, 'password': 'StrongPass123'},
    )
    assert response.status_code == 200
    payload = response.get_json()
    return payload['tokens']['access_token'], payload['tokens']['refresh_token']


def test_register_and_login_flow(client):
    email = _register_user(client)

    login = client.post(
        '/api/auth/login',
        json={'email': email, 'password': 'StrongPass123'},
    )
    assert login.status_code == 200
    data = login.get_json()
    assert 'tokens' in data
    assert 'access_token' in data['tokens']
    assert 'refresh_token' in data['tokens']


def test_auth_me_requires_access_token(client):
    email = _register_user(client)
    access_token, _ = _login_user(client, email)

    me_response = client.get('/api/auth/me', headers={'Authorization': f'Bearer {access_token}'})
    assert me_response.status_code == 200
    payload = me_response.get_json()
    assert payload['user']['email'] == email


def test_rbac_check_requires_permission(client):
    email = _register_user(client)
    access_token, _ = _login_user(client, email)

    response = client.get('/api/auth/rbac-check', headers={'Authorization': f'Bearer {access_token}'})
    assert response.status_code == 200


def test_refresh_and_logout_revoke_tokens(client):
    email = _register_user(client)
    access_token, refresh_token = _login_user(client, email)

    refresh_response = client.post('/api/auth/refresh', headers={'Authorization': f'Bearer {refresh_token}'})
    assert refresh_response.status_code == 200
    refreshed = refresh_response.get_json()['tokens']
    new_access = refreshed['access_token']

    logout_response = client.post('/api/auth/logout', headers={'Authorization': f'Bearer {new_access}'})
    assert logout_response.status_code == 200

    # Revoked access token should fail on protected endpoint
    denied = client.get('/api/auth/me', headers={'Authorization': f'Bearer {new_access}'})
    assert denied.status_code == 401


def test_status_endpoint_allows_jwt_with_dashboard_permission(client):
    email = _register_user(client)
    access_token, _ = _login_user(client, email)

    response = client.get('/api/status', headers={'Authorization': f'Bearer {access_token}'})
    assert response.status_code == 200


def test_status_endpoint_forbids_jwt_without_dashboard_permission(client, app_fixture):
    with app_fixture.app_context():
        tenant = Organization.query.filter_by(slug='default').first()
        if tenant is None:
            tenant = Organization(name='Default Organization', slug='default', is_active=True)
            db.session.add(tenant)
            db.session.flush()

        role = Role(
            organization_id=tenant.id,
            name='status-blocked-role',
            description='Role without dashboard.view',
            is_system=False,
        )
        db.session.add(role)
        db.session.flush()

        permission = Permission(code='tenant.readonly.status-test', description='Unrelated read permission')
        db.session.add(permission)
        db.session.flush()
        role.permissions.append(permission)

        user = User(
            organization_id=tenant.id,
            email='status-viewer@example.com',
            full_name='Status Viewer',
            password_hash=hash_password('StrongPass123'),
            is_active=True,
        )
        user.roles.append(role)
        db.session.add(user)
        db.session.commit()

    login = client.post(
        '/api/auth/login',
        json={'email': 'status-viewer@example.com', 'password': 'StrongPass123'},
    )
    assert login.status_code == 200
    access_token = login.get_json()['tokens']['access_token']

    denied = client.get('/api/status', headers={'Authorization': f'Bearer {access_token}'})
    assert denied.status_code == 403

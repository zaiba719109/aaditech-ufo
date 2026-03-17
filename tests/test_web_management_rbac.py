"""Tests for RBAC enforcement on web management POST routes."""

from datetime import datetime, UTC
import uuid
from unittest.mock import patch

from server.auth import get_api_key, hash_password
from server.extensions import db
from server.models import Organization, Permission, Role, SystemData, User


def _api_key_headers(extra=None):
    headers = {'X-API-Key': get_api_key()}
    if extra:
        headers.update(extra)
    return headers


def _register_admin_and_login(client, email=None):
    if email is None:
        email = f"web-admin-{uuid.uuid4().hex[:8]}@tenant.local"

    register = client.post(
        '/api/auth/register',
        headers=_api_key_headers(),
        json={
            'email': email,
            'full_name': 'Web Admin',
            'password': 'StrongPass123',
        },
    )
    assert register.status_code == 201

    login = client.post(
        '/api/auth/login',
        json={'email': email, 'password': 'StrongPass123'},
    )
    assert login.status_code == 200
    return login.get_json()['tokens']['access_token']


def _create_custom_user(client, app_fixture, permission_codes=None, email=None):
    if permission_codes is None:
        permission_codes = []
    if email is None:
        email = f"viewer-{uuid.uuid4().hex[:8]}@tenant.local"

    with app_fixture.app_context():
        tenant = Organization.query.filter_by(slug='default').first()
        if tenant is None:
            tenant = Organization(name='Default Organization', slug='default', is_active=True)
            db.session.add(tenant)
            db.session.flush()

        role = Role(
            organization_id=tenant.id,
            name=f"role-{uuid.uuid4().hex[:8]}",
            description='Custom role for web route authorization tests',
            is_system=False,
        )
        db.session.add(role)
        db.session.flush()

        for permission_code in permission_codes:
            permission = Permission(
                code=permission_code,
                description=f'Permission {permission_code}',
            )
            db.session.add(permission)
            db.session.flush()
            role.permissions.append(permission)

        user = User(
            organization_id=tenant.id,
            email=email,
            full_name='Custom User',
            password_hash=hash_password('StrongPass123'),
            is_active=True,
        )
        user.roles.append(role)
        db.session.add(user)
        db.session.commit()

    login = client.post(
        '/api/auth/login',
        json={'email': email, 'password': 'StrongPass123'},
    )
    assert login.status_code == 200
    return login.get_json()['tokens']['access_token']


def test_manual_submit_requires_authentication(client):
    response = client.post('/manual_submit')
    assert response.status_code == 401


def test_manual_submit_allows_jwt_with_permission(client):
    access_token = _register_admin_and_login(client)
    system_data = {
        'serial_number': f"SER-{uuid.uuid4().hex[:8]}",
        'hostname': 'managed-host',
        'cpu_usage': 22.5,
        'ram_usage': 38.0,
        'last_update': datetime.now(UTC),
        'status': 'active',
    }

    with patch('server.blueprints.web.SystemService.get_local_system_data', return_value=system_data):
        response = client.post('/manual_submit', headers={'Authorization': f'Bearer {access_token}'})

    assert response.status_code == 200
    assert response.get_json()['status'] == 'success'


def test_manual_submit_forbids_jwt_without_permission(client, app_fixture):
    access_token = _create_custom_user(
        client,
        app_fixture,
        permission_codes=[f"dashboard.readonly.{uuid.uuid4().hex[:8]}"],
    )

    response = client.post('/manual_submit', headers={'Authorization': f'Bearer {access_token}'})
    assert response.status_code == 403


def test_backup_create_allows_jwt_with_permission(client):
    access_token = _register_admin_and_login(client)

    with patch(
        'server.blueprints.web.BackupService.create_backup',
        return_value={'success': True, 'backup_filename': 'backup_20260316_120000.db'}
    ):
        response = client.post('/backup/create', headers={'Authorization': f'Bearer {access_token}'})

    assert response.status_code == 200
    assert response.get_json()['status'] == 'success'


def test_backup_restore_allows_jwt_with_permission(client):
    access_token = _register_admin_and_login(client)

    with patch(
        'server.blueprints.web.BackupService.restore_backup',
        return_value={'success': True, 'message': 'Database restored successfully'}
    ):
        response = client.post(
            '/backup/restore/backup_20260316_120000.db',
            headers={'Authorization': f'Bearer {access_token}'},
        )

    assert response.status_code == 200
    assert response.get_json()['status'] == 'success'


def test_backup_routes_forbid_jwt_without_permission(client, app_fixture):
    access_token = _create_custom_user(
        client,
        app_fixture,
        permission_codes=[f"system.readonly.{uuid.uuid4().hex[:8]}"],
    )

    create_response = client.post('/backup/create', headers={'Authorization': f'Bearer {access_token}'})
    restore_response = client.post(
        '/backup/restore/example.db',
        headers={'Authorization': f'Bearer {access_token}'},
    )

    assert create_response.status_code == 403
    assert restore_response.status_code == 403


def test_web_system_json_endpoints_require_authentication(client):
    list_response = client.get('/api/systems')
    detail_response = client.get('/api/system/1')

    assert list_response.status_code == 401
    assert detail_response.status_code == 401


def test_web_system_json_endpoints_allow_jwt_with_permission(client, app_fixture):
    access_token = _register_admin_and_login(client)

    with app_fixture.app_context():
        tenant = Organization.query.filter_by(slug='default').first()
        system = SystemData(
            organization_id=tenant.id,
            serial_number=f"SYS-{uuid.uuid4().hex[:8]}",
            hostname='json-managed-host',
            cpu_usage=30.0,
            ram_usage=45.0,
            last_update=datetime.now(UTC),
            status='active',
        )
        db.session.add(system)
        db.session.commit()
        system_id = system.id

    list_response = client.get('/api/systems', headers={'Authorization': f'Bearer {access_token}'})
    detail_response = client.get(f'/api/system/{system_id}', headers={'Authorization': f'Bearer {access_token}'})

    assert list_response.status_code == 200
    assert detail_response.status_code == 200
    assert detail_response.get_json()['system']['id'] == system_id


def test_web_system_json_endpoints_forbid_jwt_without_permission(client, app_fixture):
    access_token = _create_custom_user(
        client,
        app_fixture,
        permission_codes=[f"system.readonly.{uuid.uuid4().hex[:8]}"],
    )

    list_response = client.get('/api/systems', headers={'Authorization': f'Bearer {access_token}'})
    detail_response = client.get('/api/system/1', headers={'Authorization': f'Bearer {access_token}'})

    assert list_response.status_code == 403
    assert detail_response.status_code == 403
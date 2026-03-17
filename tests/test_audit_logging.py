"""Tests for structured audit logging on sensitive actions."""

import logging
import uuid
from datetime import UTC, datetime
from unittest.mock import patch

from server.auth import get_api_key
from server.models import AuditEvent


def _api_key_headers(extra=None):
    headers = {'X-API-Key': get_api_key()}
    if extra:
        headers.update(extra)
    return headers


def _register_user(client, email=None):
    if email is None:
        email = f"audit-user-{uuid.uuid4().hex[:8]}@tenant.local"

    response = client.post(
        '/api/auth/register',
        headers=_api_key_headers(),
        json={
            'email': email,
            'full_name': 'Audit User',
            'password': 'StrongPass123',
        },
    )
    assert response.status_code == 201
    return email


def test_audit_log_emitted_for_auth_login_success(client, caplog):
    email = _register_user(client)

    caplog.clear()
    caplog.set_level(logging.INFO, logger='audit')

    response = client.post(
        '/api/auth/login',
        json={'email': email, 'password': 'StrongPass123'},
    )
    assert response.status_code == 200

    messages = [record.getMessage() for record in caplog.records if record.name == 'audit']
    assert any('"action": "auth.login"' in msg and '"outcome": "success"' in msg for msg in messages)


def test_audit_event_persisted_for_auth_login(client, app_fixture):
    email = _register_user(client, email=f"audit-db-login-{uuid.uuid4().hex[:8]}@tenant.local")

    before_count = None
    with app_fixture.app_context():
        before_count = AuditEvent.query.filter_by(action='auth.login').count()

    response = client.post(
        '/api/auth/login',
        json={'email': email, 'password': 'StrongPass123'},
    )
    assert response.status_code == 200

    with app_fixture.app_context():
        after_count = AuditEvent.query.filter_by(action='auth.login').count()
        latest = AuditEvent.query.filter_by(action='auth.login').order_by(AuditEvent.id.desc()).first()

    assert after_count == before_count + 1
    assert latest is not None
    assert latest.outcome == 'success'
    assert latest.path == '/api/auth/login'


def test_audit_log_emitted_for_tenant_create(client, caplog):
    caplog.clear()
    caplog.set_level(logging.INFO, logger='audit')

    response = client.post(
        '/api/tenants',
        headers=_api_key_headers(),
        json={'name': 'Audit Tenant', 'slug': f"audit-tenant-{uuid.uuid4().hex[:6]}"},
    )
    assert response.status_code == 201

    messages = [record.getMessage() for record in caplog.records if record.name == 'audit']
    assert any('"action": "tenant.create"' in msg and '"outcome": "success"' in msg for msg in messages)


def test_audit_log_emitted_for_manual_submit(client, caplog):
    email = _register_user(client, email=f"audit-manual-{uuid.uuid4().hex[:8]}@tenant.local")
    login = client.post('/api/auth/login', json={'email': email, 'password': 'StrongPass123'})
    assert login.status_code == 200
    access_token = login.get_json()['tokens']['access_token']

    system_data = {
        'serial_number': f"AUDIT-{uuid.uuid4().hex[:8]}",
        'hostname': 'audit-host',
        'cpu_usage': 21.0,
        'ram_usage': 34.0,
        'last_update': datetime.now(UTC),
        'status': 'active',
    }

    caplog.clear()
    caplog.set_level(logging.INFO, logger='audit')

    with patch('server.blueprints.web.SystemService.get_local_system_data', return_value=system_data):
        response = client.post('/manual_submit', headers={'Authorization': f'Bearer {access_token}'})

    assert response.status_code == 200
    messages = [record.getMessage() for record in caplog.records if record.name == 'audit']
    assert any('"action": "system.manual_submit"' in msg and '"outcome": "success"' in msg for msg in messages)


def test_audit_log_emitted_for_backup_create(client, caplog):
    email = _register_user(client, email=f"audit-backup-{uuid.uuid4().hex[:8]}@tenant.local")
    login = client.post('/api/auth/login', json={'email': email, 'password': 'StrongPass123'})
    assert login.status_code == 200
    access_token = login.get_json()['tokens']['access_token']

    caplog.clear()
    caplog.set_level(logging.INFO, logger='audit')

    with patch(
        'server.blueprints.web.BackupService.create_backup',
        return_value={'success': True, 'backup_filename': 'backup_20260316_120000.db'}
    ):
        response = client.post('/backup/create', headers={'Authorization': f'Bearer {access_token}'})

    assert response.status_code == 200
    messages = [record.getMessage() for record in caplog.records if record.name == 'audit']
    assert any('"action": "backup.create"' in msg and '"outcome": "success"' in msg for msg in messages)


def test_audit_event_persisted_for_manual_submit(client, app_fixture):
    email = _register_user(client, email=f"audit-db-manual-{uuid.uuid4().hex[:8]}@tenant.local")
    login = client.post('/api/auth/login', json={'email': email, 'password': 'StrongPass123'})
    assert login.status_code == 200
    access_token = login.get_json()['tokens']['access_token']

    system_data = {
        'serial_number': f"AUDITDB-{uuid.uuid4().hex[:8]}",
        'hostname': 'audit-db-host',
        'cpu_usage': 23.0,
        'ram_usage': 36.0,
        'last_update': datetime.now(UTC),
        'status': 'active',
    }

    with app_fixture.app_context():
        before_count = AuditEvent.query.filter_by(action='system.manual_submit').count()

    with patch('server.blueprints.web.SystemService.get_local_system_data', return_value=system_data):
        response = client.post('/manual_submit', headers={'Authorization': f'Bearer {access_token}'})

    assert response.status_code == 200

    with app_fixture.app_context():
        after_count = AuditEvent.query.filter_by(action='system.manual_submit').count()
        latest = AuditEvent.query.filter_by(action='system.manual_submit').order_by(AuditEvent.id.desc()).first()

    assert after_count == before_count + 1
    assert latest is not None
    assert latest.outcome == 'success'
    assert latest.path == '/manual_submit'

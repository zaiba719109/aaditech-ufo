"""Tests for alert notification queue dispatch with retry and audit coverage."""

from datetime import datetime
from unittest.mock import patch

from server.auth import get_api_key
from server.models import AuditEvent, Organization, SystemData
from server.extensions import db


def _headers(tenant_slug=None):
    headers = {'X-API-Key': get_api_key()}
    if tenant_slug:
        headers['X-Tenant-Slug'] = tenant_slug
    return headers


def _seed_triggered_alert(client, app_fixture):
    created = client.post(
        '/api/alerts/rules',
        headers=_headers(),
        json={
            'name': 'Dispatch CPU High',
            'metric': 'cpu_usage',
            'operator': '>',
            'threshold': 80,
            'severity': 'critical',
        },
    )
    assert created.status_code == 201

    with app_fixture.app_context():
        tenant = Organization.query.filter_by(slug='default').first()
        row = SystemData(
            organization_id=tenant.id,
            serial_number='DISPATCH-SN-1',
            hostname='dispatch-host',
            cpu_usage=96.7,
            last_update=datetime.utcnow(),
            status='active',
            deleted=False,
        )
        db.session.add(row)
        db.session.commit()


def test_dispatch_notifications_retries_email_then_succeeds(client, app_fixture):
    _seed_triggered_alert(client, app_fixture)

    with patch('server.services.notification_service.NotificationService.send_email_notification') as email_mock:
        email_mock.side_effect = [RuntimeError('smtp temporary failure'), None]

        response = client.post(
            '/api/alerts/dispatch',
            headers=_headers(),
            json={'channels': ['email'], 'email_retries': 2},
        )

    assert response.status_code == 202
    payload = response.get_json()
    assert payload['status'] == 'accepted'
    assert payload['job']['inline'] is True

    result = payload['job']['result']
    assert result['failure_count'] == 0
    assert 'email' in result['delivered_channels']
    assert email_mock.call_count == 2


def test_dispatch_notifications_webhook_failure_records_audit(client, app_fixture):
    _seed_triggered_alert(client, app_fixture)

    with patch('server.services.notification_service.NotificationService.send_webhook_notification') as webhook_mock:
        webhook_mock.side_effect = RuntimeError('webhook down')

        response = client.post(
            '/api/alerts/dispatch',
            headers=_headers(),
            json={'channels': ['webhook'], 'webhook_retries': 1},
        )

    assert response.status_code == 202
    payload = response.get_json()
    assert payload['status'] == 'accepted'

    result = payload['job']['result']
    assert result['failure_count'] == 1
    assert result['failures'][0]['channel'] == 'webhook'
    assert result['failures'][0]['attempts'] == 2

    with app_fixture.app_context():
        audit_row = (
            AuditEvent.query
            .filter_by(action='alerts.dispatch.delivery')
            .order_by(AuditEvent.id.desc())
            .first()
        )

    assert audit_row is not None
    assert audit_row.outcome == 'failure'

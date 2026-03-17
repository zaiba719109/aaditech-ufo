"""Tests for Phase 2 Week 9-10 alerting API foundation."""

from datetime import datetime, UTC

from server.auth import get_api_key
from server.extensions import db
from server.models import Organization, SystemData


def _headers(tenant_slug=None):
    headers = {'X-API-Key': get_api_key()}
    if tenant_slug:
        headers['X-Tenant-Slug'] = tenant_slug
    return headers


def test_create_alert_rule_success(client, app_fixture):
    response = client.post(
        '/api/alerts/rules',
        headers=_headers(),
        json={
            'name': 'CPU Critical',
            'metric': 'cpu_usage',
            'operator': '>=',
            'threshold': 90,
            'severity': 'critical',
            'is_active': True,
        },
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload['status'] == 'success'
    assert payload['rule']['name'] == 'CPU Critical'

    with app_fixture.app_context():
        assert payload['rule']['id'] is not None


def test_alert_rules_are_tenant_scoped(client, app_fixture):
    with app_fixture.app_context():
        beta = Organization(name='Beta Tenant', slug='beta-tenant', is_active=True)
        db.session.add(beta)
        db.session.commit()

    create_beta = client.post(
        '/api/alerts/rules',
        headers=_headers('beta-tenant'),
        json={
            'name': 'Beta CPU Warn',
            'metric': 'cpu_usage',
            'operator': '>',
            'threshold': 80,
            'severity': 'warning',
        },
    )
    assert create_beta.status_code == 201

    default_list = client.get('/api/alerts/rules', headers=_headers())
    assert default_list.status_code == 200
    default_names = {rule['name'] for rule in default_list.get_json()['rules']}
    assert 'Beta CPU Warn' not in default_names

    beta_list = client.get('/api/alerts/rules', headers=_headers('beta-tenant'))
    assert beta_list.status_code == 200
    beta_names = {rule['name'] for rule in beta_list.get_json()['rules']}
    assert 'Beta CPU Warn' in beta_names


def test_update_alert_rule_success(client):
    created = client.post(
        '/api/alerts/rules',
        headers=_headers(),
        json={
            'name': 'RAM High',
            'metric': 'ram_usage',
            'operator': '>',
            'threshold': 70,
            'severity': 'warning',
        },
    )
    assert created.status_code == 201
    rule_id = created.get_json()['rule']['id']

    updated = client.patch(
        f'/api/alerts/rules/{rule_id}',
        headers=_headers(),
        json={
            'threshold': 85,
            'severity': 'critical',
        },
    )
    assert updated.status_code == 200

    payload = updated.get_json()
    assert payload['rule']['threshold'] == 85.0
    assert payload['rule']['severity'] == 'critical'


def test_evaluate_alert_rules_returns_triggered_alerts(client, app_fixture):
    rule_response = client.post(
        '/api/alerts/rules',
        headers=_headers(),
        json={
            'name': 'CPU > 80',
            'metric': 'cpu_usage',
            'operator': '>',
            'threshold': 80,
            'severity': 'warning',
        },
    )
    assert rule_response.status_code == 201

    with app_fixture.app_context():
        default_tenant = Organization.query.filter_by(slug='default').first()
        assert default_tenant is not None

        system_row = SystemData(
            organization_id=default_tenant.id,
            serial_number='ALERT-SN-001',
            hostname='alert-host',
            cpu_usage=91.2,
            last_update=datetime.now(UTC).replace(tzinfo=None),
            status='active',
            deleted=False,
        )
        db.session.add(system_row)
        db.session.commit()

    evaluate = client.post('/api/alerts/evaluate', headers=_headers())
    assert evaluate.status_code == 200
    payload = evaluate.get_json()

    assert payload['status'] == 'success'
    assert payload['triggered_count'] >= 1
    assert any(alert['metric'] == 'cpu_usage' for alert in payload['alerts'])

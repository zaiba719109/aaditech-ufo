"""Tests for asynchronous maintenance workflows (Phase 1 Week 8 closeout)."""

from datetime import datetime, timedelta

from server.auth import get_api_key
from server.models import AuditEvent, RevokedToken


def _api_headers():
    return {'X-API-Key': get_api_key()}


def test_enqueue_cleanup_revoked_tokens_removes_expired_rows(client, db_session):
    expired = RevokedToken(
        jti='expired-jti-1',
        token_type='refresh',
        expires_at=datetime.utcnow() - timedelta(days=2),
    )
    active = RevokedToken(
        jti='active-jti-1',
        token_type='refresh',
        expires_at=datetime.utcnow() + timedelta(days=2),
    )
    db_session.add_all([expired, active])
    db_session.commit()

    response = client.post(
        '/api/jobs/maintenance',
        json={'job': 'cleanup_revoked_tokens'},
        headers=_api_headers(),
    )

    assert response.status_code == 202
    payload = response.get_json()
    assert payload['status'] == 'accepted'
    assert payload['job']['job_name'] == 'cleanup_revoked_tokens'

    remaining_jtis = {row.jti for row in RevokedToken.query.all()}
    assert 'expired-jti-1' not in remaining_jtis
    assert 'active-jti-1' in remaining_jtis


def test_enqueue_purge_audit_events_respects_retention_days(client, db_session):
    now = datetime.utcnow()
    old_event = AuditEvent(
        action='auth.login',
        outcome='success',
        created_at=now - timedelta(days=40),
    )
    recent_event = AuditEvent(
        action='auth.login',
        outcome='success',
        created_at=now - timedelta(days=5),
    )
    db_session.add_all([old_event, recent_event])
    db_session.commit()
    old_event_id = old_event.id
    recent_event_id = recent_event.id

    response = client.post(
        '/api/jobs/maintenance',
        json={'job': 'purge_audit_events', 'retention_days': 30},
        headers=_api_headers(),
    )

    assert response.status_code == 202
    payload = response.get_json()
    assert payload['job']['job_name'] == 'purge_audit_events'

    remaining_ids = {row.id for row in AuditEvent.query.all()}
    assert old_event_id not in remaining_ids
    assert recent_event_id in remaining_ids


def test_enqueue_maintenance_unknown_job_rejected(client):
    response = client.post(
        '/api/jobs/maintenance',
        json={'job': 'invalid_job'},
        headers=_api_headers(),
    )

    assert response.status_code == 400
    payload = response.get_json()
    assert payload['error'] == 'Validation failed'

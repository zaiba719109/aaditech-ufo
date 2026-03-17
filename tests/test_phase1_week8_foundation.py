"""Phase 1 Week 8 foundation tests: queue and gateway readiness."""

from server.auth import get_api_key


def _auth_headers(extra=None):
    headers = {'X-API-Key': get_api_key()}
    if extra:
        headers.update(extra)
    return headers


def test_gateway_request_id_headers_are_returned(client):
    inbound_request_id = 'req-week8-1234'
    response = client.get('/health', headers={'X-Request-ID': inbound_request_id})

    assert response.status_code == 200
    assert response.headers.get('X-Request-ID') == inbound_request_id
    assert response.headers.get('X-API-Gateway-Ready') == 'true'
    assert 'X-Response-Time-Ms' in response.headers


def test_status_exposes_queue_and_gateway_fields(client):
    response = client.get('/api/status', headers=_auth_headers())

    assert response.status_code == 200
    payload = response.get_json()
    assert 'queue' in payload
    assert 'gateway' in payload
    assert 'enabled' in payload['queue']
    assert 'state' in payload['queue']
    assert payload['gateway']['proxy_fix_enabled'] is True

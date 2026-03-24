"""
Unit tests for authentication module
Tests for API key validation and authentication decorator
"""

import pytest
from datetime import datetime
from unittest.mock import patch
from server.auth import require_api_key, validate_api_key, get_api_key


class TestAuthModule:
    """Test authentication module"""
    
    def test_get_api_key_from_env(self):
        """Test get_api_key() returns a non-empty string from module config"""
        key = get_api_key()
        assert key is not None
        assert isinstance(key, str)
        assert len(key) > 0
    
    def test_get_api_key_default(self):
        """Test getting default API key when not set"""
        with patch.dict('os.environ', {}, clear=False):
            # Remove AGENT_API_KEY if it exists
            if 'AGENT_API_KEY' in __import__('os').environ:
                del __import__('os').environ['AGENT_API_KEY']
            key = get_api_key()
            # Should return something, either env value or default
            assert key is not None
            assert isinstance(key, str)
    
    def test_validate_api_key_valid(self):
        """Test validating the actual configured API key succeeds"""
        # AGENT_API_KEY is a module-level constant captured at import time.
        # Directly compare against the value get_api_key() returns.
        actual_key = get_api_key()
        result = validate_api_key(actual_key)
        assert result is True
    
    def test_validate_api_key_invalid(self):
        """Test validating incorrect API key"""
        result = validate_api_key('definitely-wrong-key-xyz')
        assert result is False
    
    def test_validate_api_key_empty(self):
        """Test validating empty API key"""
        result = validate_api_key('')
        assert result is False
    
    def test_require_api_key_decorator_present(self, client):
        """Test require_api_key decorator accepts the correct API key"""
        # Test against a protected endpoint with valid auth
        response = client.post(
            '/api/submit_data',
            headers={'X-API-Key': get_api_key(), 'X-Tenant-Slug': 'default'},
            json={
                'serial_number': 'AUTH-TEST-001',
                'hostname': 'test-host',
                'last_update': datetime.utcnow().isoformat(),
                'status': 'success'
            }
        )
        # Should succeed (200/201) or fail validation (400/422), but not auth (401)
        assert response.status_code in [200, 201, 400, 422]
    
    def test_require_api_key_decorator_missing(self, client):
        """Test that protected route rejects requests without API key header"""
        # Try to post to protected endpoint without API key
        response = client.post(
            '/api/submit_data',
            headers={'X-Tenant-Slug': 'default'},
            json={
                'serial_number': 'AUTH-TEST-002',
                'hostname': 'test-host',
                'last_update': datetime.utcnow().isoformat(),
                'status': 'success'
            }
        )
        # Without API-Key header, should get 401
        assert response.status_code == 401


class TestAuthIntegration:
    """Integration tests for authentication"""
    
    def test_api_endpoint_requires_auth(self, client):
        """Test that API endpoints require authentication"""
        # Try accessing protected endpoint without auth key
        response = client.post(
            '/api/submit_data',
            headers={'X-Tenant-Slug': 'default'},
            json={
                'serial_number': 'AUTH-TEST-003',
                'hostname': 'test-host',
                'last_update': datetime.utcnow().isoformat(),
                'status': 'success'
            }
        )
        # Should be rejected without auth key
        assert response.status_code == 401
    
    def test_api_endpoint_accepts_valid_auth(self, client):
        """Test that API endpoints accept valid authentication"""
        response = client.post(
            '/api/submit_data',
            headers={'X-API-Key': get_api_key(), 'X-Tenant-Slug': 'default'},
            json={
                'serial_number': 'AUTH-TEST-004',
                'hostname': 'test-host',
                'last_update': datetime.utcnow().isoformat(),
                'status': 'success'
            }
        )
        # Should succeed (200/201) or fail validation (400/422), but not auth (401)
        assert response.status_code in [200, 201, 400, 422]

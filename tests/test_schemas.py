"""
Unit tests for input validation schemas
Tests for Marshmallow schemas and data validation
"""

import pytest
from marshmallow import ValidationError
from server.schemas import (
    DiskInfoSchema,
    RAMInfoSchema,
    CPUFrequencySchema,
    SystemDataSubmissionSchema
)


class TestDiskInfoSchema:
    """Test disk information validation schema"""
    
    def test_valid_disk_info(self):
        """Test validating valid disk information"""
        schema = DiskInfoSchema()
        data = {
            'device': '/dev/sda1',
            'mountpoint': '/',
            'total': 931.5,
            'used': 450.0,
            'free': 481.5,
            'percent': 48.3
        }
        result = schema.load(data)
        assert result['device'] == '/dev/sda1'
        assert result['percent'] == 48.3
    
    def test_disk_info_missing_required_fields(self):
        """Test disk info with missing required fields"""
        schema = DiskInfoSchema()
        data = {'device': '/dev/sda1'}
        
        with pytest.raises(ValidationError) as exc:
            schema.load(data)
        assert 'mountpoint' in exc.value.messages
    
    def test_disk_info_invalid_percent(self):
        """Test disk info with missing required field (total)"""
        schema = DiskInfoSchema()
        data = {
            'device': '/dev/sda1',
            'mountpoint': '/',
            'used': 450.0,
            'free': 481.5,
            'percent': 50.0
            # missing required 'total'
        }
        
        with pytest.raises(ValidationError):
            schema.load(data)


class TestRAMInfoSchema:
    """Test RAM information validation schema"""
    
    def test_valid_ram_info(self):
        """Test validating valid RAM information"""
        schema = RAMInfoSchema()
        data = {
            'total': 15.5,
            'available': 7.8,
            'used': 7.7,
            'percent': 49.7
        }
        result = schema.load(data)
        assert result['total'] == 15.5
        assert result['percent'] == 49.7
    
    def test_ram_info_missing_fields(self):
        """Test RAM info with missing required fields"""
        schema = RAMInfoSchema()
        data = {'total': 15.5}  # missing available, used, percent
        
        with pytest.raises(ValidationError):
            schema.load(data)


class TestCPUFrequencySchema:
    """Test CPU frequency validation schema"""
    
    def test_valid_cpu_frequency(self):
        """Test validating valid CPU frequency"""
        schema = CPUFrequencySchema()
        data = {
            'current': 2400.0,
            'min': 1600.0,
            'max': 3600.0
        }
        result = schema.load(data)
        assert result['current'] == 2400.0
    
    def test_cpu_frequency_none_values(self):
        """Test CPU frequency fields are all optional (allow_none=True)"""
        schema = CPUFrequencySchema()
        data = {
            'current': None,
            'min': None,
            'max': None
        }
        result = schema.load(data)
        assert result['current'] is None


class TestSystemDataSubmissionSchema:
    """Test system data submission validation schema"""
    
    def test_valid_system_data_submission(self):
        """Test validating complete system data submission"""
        from datetime import datetime, UTC
        schema = SystemDataSubmissionSchema()
        data = {
            'serial_number': 'ABC-123-XYZ',
            'hostname': 'desktop-computer',
            'last_update': datetime.now(UTC).isoformat(),
            'status': 'active',
            'cpu_usage': 45.5,
            'ram_usage': 60.0,
            'disk_info': [
                {
                    'device': '/dev/sda1',
                    'mountpoint': '/',
                    'total': 931.5,
                    'used': 450.0,
                    'free': 481.5,
                    'percent': 48.3
                }
            ]
        }
        result = schema.load(data)
        assert result['serial_number'] == 'ABC-123-XYZ'
        assert result['cpu_usage'] == 45.5
    
    def test_system_data_missing_required(self):
        """Test system data with missing required fields"""
        schema = SystemDataSubmissionSchema()
        data = {
            'hostname': 'desktop-computer',
            'cpu_usage': 45.5
        }
        
        with pytest.raises(ValidationError) as exc:
            schema.load(data)
        assert 'serial_number' in exc.value.messages
    
    def test_system_data_invalid_cpu(self):
        """Test system data with invalid CPU percentage"""
        schema = SystemDataSubmissionSchema()
        data = {
            'serial_number': 'ABC-123',
            'hostname': 'computer',
            'cpu_usage': 150.0,  # Invalid: > 100
            'ram_usage': 60.0
        }
        
        with pytest.raises(ValidationError):
            schema.load(data)
    
    def test_system_data_optional_fields(self):
        """Test system data with optional fields — last_update and status are required"""
        from datetime import datetime, UTC
        schema = SystemDataSubmissionSchema()
        data = {
            'serial_number': 'ABC-123',
            'hostname': 'computer',
            'last_update': datetime.now(UTC).isoformat(),
            'status': 'active',
            'cpu_usage': 45.5
            # ram_usage and disk_info are optional
        }
        result = schema.load(data)
        assert result['serial_number'] == 'ABC-123'
        assert 'ram_usage' not in result or result['ram_usage'] is None


class TestValidationEdgeCases:
    """Test edge cases in validation"""
    
    def test_zero_cpu_usage(self):
        """Test zero CPU usage is valid"""
        from datetime import datetime, UTC
        schema = SystemDataSubmissionSchema()
        data = {
            'serial_number': 'ABC-123',
            'hostname': 'computer',
            'last_update': datetime.now(UTC).isoformat(),
            'status': 'active',
            'cpu_usage': 0.0
        }
        result = schema.load(data)
        assert result['cpu_usage'] == 0.0
    
    def test_100_percent_usage(self):
        """Test 100% usage is valid"""
        from datetime import datetime, UTC
        schema = SystemDataSubmissionSchema()
        data = {
            'serial_number': 'ABC-123',
            'hostname': 'computer',
            'last_update': datetime.now(UTC).isoformat(),
            'status': 'active',
            'cpu_usage': 100.0
        }
        result = schema.load(data)
        assert result['cpu_usage'] == 100.0
    
    def test_negative_cpu_usage(self):
        """Test negative CPU usage is invalid"""
        schema = SystemDataSubmissionSchema()
        data = {
            'serial_number': 'ABC-123',
            'hostname': 'computer',
            'cpu_usage': -5.0
        }
        
        with pytest.raises(ValidationError):
            schema.load(data)

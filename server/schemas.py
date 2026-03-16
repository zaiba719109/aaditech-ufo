# server/schemas.py
"""
Input Validation Schemas
Using Marshmallow for request/response validation
"""

from marshmallow import Schema, fields, ValidationError, validates
import logging

logger = logging.getLogger(__name__)


class DiskInfoSchema(Schema):
    """Schema for disk information"""
    device = fields.Str(required=True)
    mountpoint = fields.Str(required=True)
    total = fields.Float(required=True)
    used = fields.Float(required=True)
    free = fields.Float(required=True)
    percent = fields.Float(required=True)


class RAMInfoSchema(Schema):
    """Schema for RAM information"""
    total = fields.Float(required=True)
    available = fields.Float(required=True)
    used = fields.Float(required=True)
    percent = fields.Float(required=True)


class CPUFrequencySchema(Schema):
    """Schema for CPU frequency information"""
    current = fields.Float(allow_none=True)
    min = fields.Float(allow_none=True)
    max = fields.Float(allow_none=True)


class SystemDataSubmissionSchema(Schema):
    """
    Schema for validating system data submissions from agents.
    Used to validate POST requests to /api/submit_data
    """
    
    # Required fields
    serial_number = fields.Str(required=True, validate=lambda x: len(x) > 0)
    hostname = fields.Str(required=True, validate=lambda x: len(x) > 0)
    last_update = fields.DateTime(required=True)
    status = fields.Str(required=True, validate=lambda x: x in ['active', 'inactive'])
    
    # Optional fields - System information
    model_number = fields.Str(allow_none=True)
    ip_address = fields.Str(allow_none=True)
    local_ip = fields.Str(allow_none=True)
    public_ip = fields.Str(allow_none=True)
    current_user = fields.Str(allow_none=True)
    
    # CPU information
    cpu_info = fields.Str(allow_none=True)
    cpu_cores = fields.Int(allow_none=True, validate=lambda x: x > 0 if x else True)
    cpu_threads = fields.Int(allow_none=True, validate=lambda x: x > 0 if x else True)
    cpu_usage = fields.Float(allow_none=True, validate=lambda x: 0 <= x <= 100 if x else True)
    cpu_per_core = fields.List(fields.Float(), allow_none=True)
    cpu_frequency = fields.Nested(CPUFrequencySchema, allow_none=True)
    
    # RAM information
    ram_usage = fields.Float(allow_none=True, validate=lambda x: 0 <= x <= 100 if x else True)
    ram_info = fields.Nested(RAMInfoSchema, allow_none=True)
    
    # Disk information
    disk_info = fields.List(fields.Nested(DiskInfoSchema), allow_none=True)
    storage_usage = fields.Float(allow_none=True, validate=lambda x: 0 <= x <= 100 if x else True)
    
    # Benchmark information
    software_benchmark = fields.Float(allow_none=True)
    hardware_benchmark = fields.Float(allow_none=True)
    overall_benchmark = fields.Float(allow_none=True)


def validate_system_data(data):
    """
    Validate system data submission.
    
    Args:
        data: Dictionary of system data
    
    Returns:
        Tuple of (is_valid, errors_dict)
    
    Raises:
        ValidationError: If validation fails
    """
    schema = SystemDataSubmissionSchema()
    try:
        result = schema.load(data)
        logger.debug(f"System data validation successful")
        return True, result
    except ValidationError as err:
        logger.warning(f"System data validation failed: {err.messages}")
        return False, err.messages


def validate_and_clean_system_data(data):
    """
    Validate and clean system data for storage.
    
    Args:
        data: Raw system data dictionary
    
    Returns:
        Cleaned data dictionary or raises ValidationError
    """
    is_valid, result = validate_system_data(data)
    if not is_valid:
        raise ValidationError(f"Validation failed: {result}")
    return result

"""
API Blueprint
REST API endpoints for agent data submission and system management
"""

import logging
import re
from flask import current_app
from flask import Blueprint, request, jsonify, g
from sqlalchemy import text
from ..extensions import limiter
from ..auth import (
    require_api_key,
    hash_password,
    verify_password,
    issue_jwt_tokens,
    require_refresh_token,
    require_jwt_auth,
    require_permission,
    require_api_key_or_permission,
    revoke_token,
)
from ..schemas import validate_and_clean_system_data
from ..models import db, SystemData, Organization, User, Role, Permission
from ..audit import log_audit_event
from ..queue import get_queue_status, enqueue_maintenance_job, enqueue_alert_notification_job
from ..services import AlertService
from marshmallow import ValidationError

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api')


def _slugify(name: str) -> str:
    """Convert tenant/org name to a URL-safe slug."""
    normalized = re.sub(r'[^a-zA-Z0-9\s-]', '', name).strip().lower()
    return re.sub(r'[\s_-]+', '-', normalized).strip('-')


def _get_or_create_permission(code: str, description: str = '') -> Permission:
    permission = Permission.query.filter_by(code=code).first()
    if permission:
        return permission
    permission = Permission(code=code, description=description)
    db.session.add(permission)
    db.session.flush()
    return permission


def _get_or_create_default_admin_role(organization_id: int) -> Role:
    role = Role.query.filter_by(organization_id=organization_id, name='admin').first()
    if not role:
        role = Role(
            organization_id=organization_id,
            name='admin',
            description='Default tenant administrator role',
            is_system=True,
        )

        db.session.add(role)
        db.session.flush()

    existing_codes = {permission.code for permission in role.permissions}
    required_permissions = [
        ('tenant.manage', 'Manage tenant settings and users'),
        ('dashboard.view', 'View dashboard data'),
        ('system.submit', 'Submit or refresh local system data'),
        ('backup.manage', 'Create and restore backups'),
    ]

    for code, description in required_permissions:
        if code not in existing_codes:
            role.permissions.append(_get_or_create_permission(code, description))

    return role


@api_bp.route('/submit_data', methods=['POST'])
@limiter.limit("10 per minute")
@require_api_key
def submit_data():
    """
    Submit system data from agent.
    
    Request JSON:
        - serial_number: System serial number (required)
        - hostname: System hostname (required)
        - system_info: System hardware details (required)
        - performance_metrics: CPU, RAM, disk metrics (required)
        - benchmark_results: Benchmark scores (required)
        - last_update: Last update timestamp (required)
        - status: System status (required)
    
    Returns:
        - 200: Success with submitted data
        - 400: Validation error
        - 401: Missing API key
        - 403: Invalid API key
        - 429: Rate limit exceeded
        - 500: Server error
    """
    try:
        data = request.get_json() or {}
        
        # Log incoming data
        logger.info(f"Received data submission from {request.remote_addr}")
        
        # Validate input data
        try:
            validated_data = validate_and_clean_system_data(data)
        except ValidationError as e:
            logger.warning(f"Validation error: {e.messages}")
            return jsonify({
                'error': 'Validation failed',
                'details': e.messages
            }), 400
        
        # Create and save new system data record
        validated_data['organization_id'] = g.tenant.id
        new_system = SystemData(**validated_data)
        db.session.add(new_system)
        db.session.commit()
        
        logger.info(f"Data saved for system: {validated_data.get('hostname')}")
        
        return jsonify({
            'status': 'success',
            'message': 'Data submitted successfully',
            'system_id': new_system.id
        }), 200
    
    except Exception as e:
        logger.error(f"Error submitting data: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'error': 'Data submission failed',
            'details': str(e)
        }), 500


@api_bp.route('/status', methods=['GET'])
@require_api_key_or_permission('dashboard.view')
def status():
    """
    Get API status.
    
    Returns:
        - 200: API is operational
    """
    return jsonify({
        'status': 'operational',
        'message': 'API is running',
        'version': '1.0.0',
        'queue': get_queue_status(current_app),
        'gateway': {
            'request_id': getattr(g, 'request_id', None),
            'proxy_fix_enabled': bool(current_app.config.get('ENABLE_PROXY_FIX', True)),
        },
    }), 200


@api_bp.route('/jobs/maintenance', methods=['POST'])
@limiter.limit("20 per hour")
@require_api_key_or_permission('tenant.manage')
def queue_maintenance_job():
    """Queue a maintenance workflow for asynchronous processing."""
    payload = request.get_json(silent=True) or {}
    job_name = (payload.get('job') or '').strip()

    if not job_name:
        log_audit_event('queue.maintenance.enqueue', outcome='failure', reason='job_missing')
        return jsonify({'error': 'Validation failed', 'details': {'job': ['Field required.']}}), 400

    enqueue_kwargs = {}
    if 'retention_days' in payload:
        enqueue_kwargs['retention_days'] = payload.get('retention_days')

    try:
        result = enqueue_maintenance_job(current_app, job_name, **enqueue_kwargs)
    except ValueError:
        log_audit_event('queue.maintenance.enqueue', outcome='failure', reason='unknown_job', job=job_name)
        return jsonify({'error': 'Validation failed', 'details': {'job': ['Unknown maintenance job.']}}), 400
    except Exception as exc:
        logger.error("Failed to enqueue maintenance job '%s': %s", job_name, exc, exc_info=True)
        log_audit_event('queue.maintenance.enqueue', outcome='failure', reason='enqueue_error', job=job_name)
        return jsonify({'error': 'Queue unavailable', 'details': str(exc)}), 503

    if not result.get('accepted'):
        log_audit_event(
            'queue.maintenance.enqueue',
            outcome='failure',
            reason=result.get('reason', 'queue_disabled'),
            job=job_name,
        )
        return jsonify({'error': 'Queue disabled', 'details': result}), 503

    log_audit_event(
        'queue.maintenance.enqueue',
        outcome='success',
        job=job_name,
        task_name=result.get('task_name'),
        task_id=result.get('task_id'),
    )
    return jsonify({'status': 'accepted', 'job': result}), 202


@api_bp.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint (no auth required).
    
    Returns:
        - 200: Service is healthy
    """
    try:
        # Check database connection
        db.session.execute(text('SELECT 1'))
        return jsonify({
            'status': 'healthy',
            'database': 'connected'
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }), 503


@api_bp.route('/tenants', methods=['GET'])
@require_api_key_or_permission('tenant.manage')
def list_tenants():
    """List all tenant organizations."""
    organizations = Organization.query.order_by(Organization.created_at.desc()).all()
    log_audit_event('tenant.list', outcome='success', tenant_count=len(organizations))
    return jsonify({
        'status': 'success',
        'count': len(organizations),
        'tenants': [org.to_dict() for org in organizations],
        'current_tenant': g.tenant.to_dict(),
    }), 200


@api_bp.route('/tenants', methods=['POST'])
@limiter.limit("20 per hour")
@require_api_key_or_permission('tenant.manage')
def create_tenant():
    """Create a new tenant organization."""
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    slug = (data.get('slug') or '').strip().lower()

    if not name:
        log_audit_event('tenant.create', outcome='failure', reason='name_missing')
        return jsonify({'error': 'Validation failed', 'details': {'name': ['Missing data for required field.']}}), 400

    if not slug:
        slug = _slugify(name)

    if not slug:
        log_audit_event('tenant.create', outcome='failure', reason='slug_invalid')
        return jsonify({'error': 'Validation failed', 'details': {'slug': ['Could not generate valid slug.']}}), 400

    existing = Organization.query.filter_by(slug=slug).first()
    if existing:
        log_audit_event('tenant.create', outcome='failure', reason='slug_conflict', tenant_slug=slug)
        return jsonify({'error': 'Tenant already exists', 'details': {'slug': [f"Tenant slug '{slug}' already exists."]}}), 409

    org = Organization(name=name, slug=slug, is_active=bool(data.get('is_active', True)))
    db.session.add(org)
    db.session.commit()

    logger.info("Created tenant '%s' (%s)", org.name, org.slug)
    log_audit_event('tenant.create', outcome='success', tenant_id=org.id, tenant_slug=org.slug)
    return jsonify({'status': 'success', 'tenant': org.to_dict()}), 201


@api_bp.route('/tenants/<int:tenant_id>/status', methods=['PATCH'])
@limiter.limit("30 per hour")
@require_api_key_or_permission('tenant.manage')
def update_tenant_status(tenant_id):
    """Activate or deactivate a tenant organization."""
    data = request.get_json() or {}
    if 'is_active' not in data:
        log_audit_event('tenant.status_update', outcome='failure', reason='is_active_missing', tenant_id=tenant_id)
        return jsonify({'error': 'Validation failed', 'details': {'is_active': ['Field required.']}}), 400

    org = db.session.get(Organization, tenant_id)
    if not org:
        log_audit_event('tenant.status_update', outcome='failure', reason='tenant_not_found', tenant_id=tenant_id)
        return jsonify({'error': 'Tenant not found'}), 404

    if org.slug == 'default' and data.get('is_active') is False:
        log_audit_event('tenant.status_update', outcome='failure', reason='default_tenant_deactivate_blocked', tenant_id=tenant_id)
        return jsonify({'error': 'Operation not allowed', 'details': {'tenant': ['Default tenant cannot be deactivated.']}}), 400

    org.is_active = bool(data.get('is_active'))
    db.session.commit()

    logger.info("Updated tenant status '%s' -> %s", org.slug, org.is_active)
    log_audit_event('tenant.status_update', outcome='success', tenant_id=org.id, tenant_slug=org.slug, is_active=org.is_active)
    return jsonify({'status': 'success', 'tenant': org.to_dict()}), 200


@api_bp.route('/auth/register', methods=['POST'])
@limiter.limit("30 per hour")
@require_api_key_or_permission('tenant.manage')
def register_user():
    """Register tenant-scoped user and assign default admin role."""
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    full_name = (data.get('full_name') or '').strip()
    password = (data.get('password') or '').strip()

    if not email or not full_name or not password:
        log_audit_event('auth.register', outcome='failure', reason='required_fields_missing')
        return jsonify({
            'error': 'Validation failed',
            'details': {'required': ['email', 'full_name', 'password']}
        }), 400

    if len(password) < 8:
        log_audit_event('auth.register', outcome='failure', reason='password_too_short', email=email)
        return jsonify({'error': 'Validation failed', 'details': {'password': ['Minimum length is 8']}}), 400

    existing = User.query.filter_by(organization_id=g.tenant.id, email=email).first()
    if existing:
        log_audit_event('auth.register', outcome='failure', reason='user_exists', email=email)
        return jsonify({'error': 'User already exists'}), 409

    user = User(
        organization_id=g.tenant.id,
        email=email,
        full_name=full_name,
        password_hash=hash_password(password),
        is_active=True,
    )
    admin_role = _get_or_create_default_admin_role(g.tenant.id)
    user.roles.append(admin_role)

    db.session.add(user)
    db.session.commit()

    log_audit_event('auth.register', outcome='success', created_user_id=user.id, created_user_email=user.email)

    return jsonify({
        'status': 'success',
        'user': {
            'id': user.id,
            'organization_id': user.organization_id,
            'email': user.email,
            'full_name': user.full_name,
            'roles': [role.name for role in user.roles],
        }
    }), 201


@api_bp.route('/auth/login', methods=['POST'])
@limiter.limit("60 per hour")
def login_user():
    """Login user and return JWT access/refresh tokens."""
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    password = (data.get('password') or '').strip()

    if not email or not password:
        log_audit_event('auth.login', outcome='failure', reason='required_fields_missing')
        return jsonify({'error': 'Validation failed', 'details': {'required': ['email', 'password']}}), 400

    user = User.query.filter_by(organization_id=g.tenant.id, email=email).first()
    if not user or not user.is_active:
        log_audit_event('auth.login', outcome='failure', reason='invalid_credentials', email=email)
        return jsonify({'error': 'Unauthorized', 'message': 'Invalid credentials'}), 401

    if not verify_password(password, user.password_hash):
        log_audit_event('auth.login', outcome='failure', reason='invalid_credentials', email=email)
        return jsonify({'error': 'Unauthorized', 'message': 'Invalid credentials'}), 401

    tokens = issue_jwt_tokens(user)
    log_audit_event('auth.login', outcome='success', user_id=user.id, user_email=user.email)
    return jsonify({
        'status': 'success',
        'tokens': tokens,
        'user': {
            'id': user.id,
            'organization_id': user.organization_id,
            'email': user.email,
            'full_name': user.full_name,
            'roles': [role.name for role in user.roles],
        }
    }), 200


@api_bp.route('/auth/refresh', methods=['POST'])
@require_refresh_token
def refresh_tokens():
    """Refresh JWT access + refresh tokens using refresh token."""
    revoke_token(g.jwt_payload)
    tokens = issue_jwt_tokens(g.current_user)
    log_audit_event('auth.refresh', outcome='success', user_id=g.current_user.id, user_email=g.current_user.email)
    return jsonify({'status': 'success', 'tokens': tokens}), 200


@api_bp.route('/auth/logout', methods=['POST'])
@require_jwt_auth
def logout_user():
    """Logout by revoking current access token."""
    revoke_token(g.jwt_payload)
    log_audit_event('auth.logout', outcome='success', user_id=g.current_user.id, user_email=g.current_user.email)
    return jsonify({'status': 'success', 'message': 'Logged out successfully'}), 200


@api_bp.route('/auth/me', methods=['GET'])
@require_jwt_auth
def auth_me():
    """Return authenticated user profile and permissions."""
    user = g.current_user
    permissions = sorted({p.code for role in user.roles for p in role.permissions})
    return jsonify({
        'status': 'success',
        'user': {
            'id': user.id,
            'organization_id': user.organization_id,
            'email': user.email,
            'full_name': user.full_name,
            'is_active': user.is_active,
            'roles': [role.name for role in user.roles],
            'permissions': permissions,
        }
    }), 200


@api_bp.route('/auth/rbac-check', methods=['GET'])
@require_permission('tenant.manage')
def auth_rbac_check():
    """Protected endpoint to validate RBAC permission enforcement."""
    return jsonify({'status': 'success', 'message': 'RBAC permission granted'}), 200


@api_bp.route('/alerts/rules', methods=['GET'])
@require_api_key_or_permission('tenant.manage')
def list_alert_rules():
    """List tenant-scoped alert threshold rules."""
    rules = AlertService.list_rules(g.tenant.id)
    return jsonify({
        'status': 'success',
        'count': len(rules),
        'rules': [rule.to_dict() for rule in rules],
    }), 200


@api_bp.route('/alerts/rules', methods=['POST'])
@limiter.limit("60 per hour")
@require_api_key_or_permission('tenant.manage')
def create_alert_rule():
    """Create new threshold alert rule for current tenant."""
    payload = request.get_json(silent=True) or {}
    rule, errors = AlertService.create_rule(g.tenant.id, payload)
    if errors:
        log_audit_event('alerts.rule.create', outcome='failure', reason='validation_failed', details=errors)
        return jsonify({'error': 'Validation failed', 'details': errors}), 400

    log_audit_event('alerts.rule.create', outcome='success', alert_rule_id=rule.id, metric=rule.metric)
    return jsonify({'status': 'success', 'rule': rule.to_dict()}), 201


@api_bp.route('/alerts/rules/<int:rule_id>', methods=['PATCH'])
@limiter.limit("120 per hour")
@require_api_key_or_permission('tenant.manage')
def update_alert_rule(rule_id):
    """Patch tenant alert rule fields."""
    payload = request.get_json(silent=True) or {}
    rule, errors, not_found_reason = AlertService.update_rule(g.tenant.id, rule_id, payload)

    if not_found_reason == 'not_found':
        log_audit_event('alerts.rule.update', outcome='failure', reason='not_found', alert_rule_id=rule_id)
        return jsonify({'error': 'Alert rule not found'}), 404

    if errors:
        log_audit_event('alerts.rule.update', outcome='failure', reason='validation_failed', alert_rule_id=rule_id)
        return jsonify({'error': 'Validation failed', 'details': errors}), 400

    log_audit_event('alerts.rule.update', outcome='success', alert_rule_id=rule.id)
    return jsonify({'status': 'success', 'rule': rule.to_dict()}), 200


@api_bp.route('/alerts/evaluate', methods=['POST'])
@limiter.limit("120 per hour")
@require_api_key_or_permission('dashboard.view')
def evaluate_alert_rules():
    """Evaluate active alert rules for the current tenant and return triggers."""
    triggered = AlertService.evaluate_rules_for_tenant(g.tenant.id)
    log_audit_event('alerts.evaluate', outcome='success', triggered_count=len(triggered))
    return jsonify({
        'status': 'success',
        'triggered_count': len(triggered),
        'alerts': triggered,
    }), 200


@api_bp.route('/alerts/dispatch', methods=['POST'])
@limiter.limit("60 per hour")
@require_api_key_or_permission('tenant.manage')
def dispatch_alert_notifications():
    """Queue alert notification dispatch (email/webhook) with retry-aware delivery."""
    payload = request.get_json(silent=True) or {}

    channels = payload.get('channels')
    if channels is not None and not isinstance(channels, list):
        log_audit_event('alerts.dispatch.enqueue', outcome='failure', reason='channels_invalid')
        return jsonify({'error': 'Validation failed', 'details': {'channels': ['Must be a list.']}}), 400

    alerts = payload.get('alerts')
    if alerts is not None and not isinstance(alerts, list):
        log_audit_event('alerts.dispatch.enqueue', outcome='failure', reason='alerts_invalid')
        return jsonify({'error': 'Validation failed', 'details': {'alerts': ['Must be a list.']}}), 400

    enqueue_kwargs = {
        'organization_id': g.tenant.id,
        'alerts': alerts,
        'channels': channels,
        'email_retries': payload.get('email_retries'),
        'webhook_retries': payload.get('webhook_retries'),
    }

    try:
        result = enqueue_alert_notification_job(current_app, **enqueue_kwargs)
    except Exception as exc:
        logger.error("Failed to enqueue alert dispatch: %s", exc, exc_info=True)
        log_audit_event('alerts.dispatch.enqueue', outcome='failure', reason='enqueue_error')
        return jsonify({'error': 'Queue unavailable', 'details': str(exc)}), 503

    if not result.get('accepted'):
        log_audit_event('alerts.dispatch.enqueue', outcome='failure', reason=result.get('reason', 'queue_disabled'))
        return jsonify({'error': 'Queue disabled', 'details': result}), 503

    log_audit_event(
        'alerts.dispatch.enqueue',
        outcome='success',
        task_name=result.get('task_name'),
        task_id=result.get('task_id'),
    )

    inline_result = result.get('result') if result.get('inline') else None
    if inline_result is not None:
        delivery_outcome = 'failure' if inline_result.get('failure_count', 0) > 0 else 'success'
        log_audit_event(
            'alerts.dispatch.delivery',
            outcome=delivery_outcome,
            alerts_count=inline_result.get('alerts_count', 0),
            delivered_channels=','.join(inline_result.get('delivered_channels', [])),
            failure_count=inline_result.get('failure_count', 0),
        )

    return jsonify({'status': 'accepted', 'job': result}), 202

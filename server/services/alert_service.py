"""Alerting domain service for threshold rule management and evaluation."""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from ..extensions import db
from ..models import AlertRule, SystemData


class AlertService:
    """Business logic for tenant-scoped alert rules."""

    ALLOWED_METRICS = {
        'cpu_usage',
        'ram_usage',
        'storage_usage',
        'software_benchmark',
        'hardware_benchmark',
        'overall_benchmark',
    }
    ALLOWED_OPERATORS = {'>', '>=', '<', '<=', '==', '!='}
    ALLOWED_SEVERITIES = {'info', 'warning', 'critical'}

    @staticmethod
    def list_rules(organization_id: int) -> list[AlertRule]:
        """Return all alert rules for a tenant."""
        return (
            AlertRule.query
            .filter_by(organization_id=organization_id)
            .order_by(AlertRule.created_at.desc())
            .all()
        )

    @classmethod
    def create_rule(cls, organization_id: int, payload: dict[str, Any]) -> tuple[AlertRule | None, dict[str, list[str]]]:
        """Create alert rule if payload is valid."""
        errors = cls._validate_payload(payload, partial=False)
        if errors:
            return None, errors

        rule = AlertRule(
            organization_id=organization_id,
            name=payload['name'].strip(),
            metric=payload['metric'],
            operator=payload['operator'],
            threshold=float(payload['threshold']),
            severity=payload.get('severity', 'warning'),
            is_active=bool(payload.get('is_active', True)),
        )
        db.session.add(rule)
        db.session.commit()
        return rule, {}

    @classmethod
    def update_rule(
        cls,
        organization_id: int,
        rule_id: int,
        payload: dict[str, Any],
    ) -> tuple[AlertRule | None, dict[str, list[str]], str | None]:
        """Update existing tenant rule and return (rule, errors, not_found_reason)."""
        rule = AlertRule.query.filter_by(id=rule_id, organization_id=organization_id).first()
        if not rule:
            return None, {}, 'not_found'

        errors = cls._validate_payload(payload, partial=True)
        if errors:
            return None, errors, None

        if 'name' in payload:
            rule.name = payload['name'].strip()
        if 'metric' in payload:
            rule.metric = payload['metric']
        if 'operator' in payload:
            rule.operator = payload['operator']
        if 'threshold' in payload:
            rule.threshold = float(payload['threshold'])
        if 'severity' in payload:
            rule.severity = payload['severity']
        if 'is_active' in payload:
            rule.is_active = bool(payload['is_active'])

        db.session.commit()
        return rule, {}, None

    @classmethod
    def evaluate_rules_for_tenant(cls, organization_id: int) -> list[dict[str, Any]]:
        """Evaluate active alert rules against latest active systems in tenant."""
        rules = AlertRule.query.filter_by(organization_id=organization_id, is_active=True).all()
        if not rules:
            return []

        systems = (
            SystemData.query
            .filter_by(organization_id=organization_id, deleted=False)
            .order_by(SystemData.last_update.desc())
            .all()
        )
        if not systems:
            return []

        triggered = []
        evaluated_at = datetime.now(UTC).isoformat()

        for system in systems:
            for rule in rules:
                metric_value = getattr(system, rule.metric, None)
                if metric_value is None:
                    continue

                if cls._compare(float(metric_value), rule.operator, float(rule.threshold)):
                    triggered.append({
                        'rule_id': rule.id,
                        'rule_name': rule.name,
                        'severity': rule.severity,
                        'metric': rule.metric,
                        'operator': rule.operator,
                        'threshold': rule.threshold,
                        'actual_value': float(metric_value),
                        'system_id': system.id,
                        'hostname': system.hostname,
                        'serial_number': system.serial_number,
                        'triggered_at': evaluated_at,
                    })

        return triggered

    @classmethod
    def _validate_payload(cls, payload: dict[str, Any], partial: bool) -> dict[str, list[str]]:
        errors: dict[str, list[str]] = {}

        required_fields = ['name', 'metric', 'operator', 'threshold']
        if not partial:
            for field in required_fields:
                if field not in payload:
                    errors.setdefault(field, []).append('Field required.')

        if 'name' in payload and not str(payload.get('name', '')).strip():
            errors.setdefault('name', []).append('Name cannot be empty.')

        metric = payload.get('metric')
        if metric is not None and metric not in cls.ALLOWED_METRICS:
            errors.setdefault('metric', []).append('Unsupported metric for threshold alerting.')

        operator = payload.get('operator')
        if operator is not None and operator not in cls.ALLOWED_OPERATORS:
            errors.setdefault('operator', []).append('Unsupported operator.')

        if 'threshold' in payload:
            try:
                float(payload['threshold'])
            except (TypeError, ValueError):
                errors.setdefault('threshold', []).append('Threshold must be a number.')

        severity = payload.get('severity')
        if severity is not None and severity not in cls.ALLOWED_SEVERITIES:
            errors.setdefault('severity', []).append('Severity must be one of info, warning, critical.')

        return errors

    @staticmethod
    def _compare(actual: float, operator: str, threshold: float) -> bool:
        if operator == '>':
            return actual > threshold
        if operator == '>=':
            return actual >= threshold
        if operator == '<':
            return actual < threshold
        if operator == '<=':
            return actual <= threshold
        if operator == '==':
            return actual == threshold
        if operator == '!=':
            return actual != threshold
        return False
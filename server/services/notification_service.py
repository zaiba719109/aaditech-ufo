"""Notification delivery service for alert dispatch channels."""

from __future__ import annotations

import json
import smtplib
from email.message import EmailMessage
from typing import Any
from urllib import request as urllib_request


class NotificationService:
    """Deliver alert notifications to email and webhook channels with retries."""

    @classmethod
    def dispatch_notifications(
        cls,
        alerts: list[dict[str, Any]],
        config: dict[str, Any],
        channels: list[str] | None = None,
        email_retries: int | None = None,
        webhook_retries: int | None = None,
    ) -> dict[str, Any]:
        channels = channels or ['email', 'webhook']
        email_retries = int(email_retries if email_retries is not None else config.get('email_retries', 2))
        webhook_retries = int(webhook_retries if webhook_retries is not None else config.get('webhook_retries', 2))

        if not alerts:
            return {
                'status': 'success',
                'alerts_count': 0,
                'delivered_channels': [],
                'failure_count': 0,
                'failures': [],
            }

        failures = []
        delivered_channels = []

        if 'email' in channels and config.get('email_enabled'):
            sent, attempts, error = cls._attempt_email(alerts, config, email_retries)
            if sent:
                delivered_channels.append('email')
            else:
                failures.append({'channel': 'email', 'attempts': attempts, 'error': error})

        if 'webhook' in channels and config.get('webhook_enabled'):
            sent, attempts, error = cls._attempt_webhook(alerts, config, webhook_retries)
            if sent:
                delivered_channels.append('webhook')
            else:
                failures.append({'channel': 'webhook', 'attempts': attempts, 'error': error})

        return {
            'status': 'success' if not failures else 'partial_failure',
            'alerts_count': len(alerts),
            'delivered_channels': delivered_channels,
            'failure_count': len(failures),
            'failures': failures,
        }

    @classmethod
    def _attempt_email(cls, alerts: list[dict[str, Any]], config: dict[str, Any], retries: int) -> tuple[bool, int, str | None]:
        recipients = [item.strip() for item in (config.get('email_to') or '').split(',') if item.strip()]
        if not recipients:
            return False, 0, 'No recipients configured'

        attempts = 0
        while attempts <= retries:
            attempts += 1
            try:
                cls.send_email_notification(alerts, config, recipients)
                return True, attempts, None
            except Exception as exc:
                if attempts > retries:
                    return False, attempts, str(exc)
        return False, attempts, 'Unknown email delivery error'

    @classmethod
    def _attempt_webhook(cls, alerts: list[dict[str, Any]], config: dict[str, Any], retries: int) -> tuple[bool, int, str | None]:
        webhook_url = config.get('webhook_url') or ''
        if not webhook_url:
            return False, 0, 'No webhook URL configured'

        attempts = 0
        while attempts <= retries:
            attempts += 1
            try:
                cls.send_webhook_notification(alerts, webhook_url)
                return True, attempts, None
            except Exception as exc:
                if attempts > retries:
                    return False, attempts, str(exc)
        return False, attempts, 'Unknown webhook delivery error'

    @staticmethod
    def send_email_notification(alerts: list[dict[str, Any]], config: dict[str, Any], recipients: list[str]):
        """Send a summarized alert email."""
        message = EmailMessage()
        message['Subject'] = f"AADITECH Alert Dispatch ({len(alerts)} alerts)"
        message['From'] = config.get('email_from')
        message['To'] = ', '.join(recipients)

        lines = []
        for alert in alerts:
            lines.append(
                f"- [{alert.get('severity')}] {alert.get('rule_name')} on {alert.get('hostname')}: "
                f"{alert.get('metric')} {alert.get('operator')} {alert.get('threshold')} "
                f"(actual {alert.get('actual_value')})"
            )
        message.set_content('\n'.join(lines))

        with smtplib.SMTP(config.get('smtp_host'), int(config.get('smtp_port'))):
            # Intentionally no auth in initial foundation; can be added in hardening.
            pass

    @staticmethod
    def send_webhook_notification(alerts: list[dict[str, Any]], webhook_url: str):
        """Post alert payload to configured webhook."""
        payload = json.dumps({'alerts': alerts}).encode('utf-8')
        req = urllib_request.Request(
            webhook_url,
            data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        with urllib_request.urlopen(req, timeout=5):
            pass

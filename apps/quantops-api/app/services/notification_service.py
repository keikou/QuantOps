from __future__ import annotations

import os
from typing import Any

from app.clients.v12_client import utc_now_iso
from app.repositories.audit_repository import AuditRepository


class NotificationService:
    def __init__(self, audit_repository: AuditRepository) -> None:
        self.audit_repository = audit_repository

    def get_channels(self) -> dict[str, Any]:
        slack_webhook = os.getenv('QUANTOPS_ALERT_SLACK_WEBHOOK', '').strip()
        generic_webhook = os.getenv('QUANTOPS_ALERT_WEBHOOK_URL', '').strip()
        email_to = os.getenv('QUANTOPS_ALERT_EMAIL_TO', '').strip()
        return {
            'slack_enabled': bool(slack_webhook),
            'webhook_enabled': bool(generic_webhook),
            'email_enabled': bool(email_to),
            'configured_targets': {
                'slack': 'configured' if slack_webhook else 'disabled',
                'webhook': 'configured' if generic_webhook else 'disabled',
                'email': email_to or 'disabled',
            },
            'as_of': utc_now_iso(),
        }

    def notify_risk_event(self, severity: str, message: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        event = {
            'severity': severity,
            'message': message,
            'payload': payload or {},
            'channels': self.get_channels()['configured_targets'],
            'as_of': utc_now_iso(),
        }
        self.audit_repository.log_action(
            category='notification',
            event_type='risk_alert_notify',
            payload_json=str(event),
        )
        return {'ok': True, 'delivered': False, 'event': event}

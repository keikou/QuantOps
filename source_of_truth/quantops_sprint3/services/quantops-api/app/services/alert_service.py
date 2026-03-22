from __future__ import annotations

import json

from app.repositories.alert_repository import AlertRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.risk_repository import RiskRepository


class AlertService:
    def __init__(self, repository: AlertRepository, audit_repository: AuditRepository, risk_repository: RiskRepository) -> None:
        self.repository = repository
        self.audit_repository = audit_repository
        self.risk_repository = risk_repository

    def evaluate_rules(self) -> dict:
        latest = self.risk_repository.latest_snapshot()
        created = []
        if latest and float(latest.get("drawdown", 0.0) or 0.0) >= 0.05:
            created.append(self.repository.create_alert({
                "alert_type": "drawdown_breach",
                "severity": "high",
                "source_service": "risk",
                "title": "Drawdown threshold breached",
                "message": f"drawdown={latest.get('drawdown')}",
                "payload": latest,
            }))
        return {"ok": True, "created": created}

    def list_alerts(self) -> dict:
        return {"count": len(self.repository.list_alerts()), "items": self.repository.list_alerts()}

    def acknowledge(self, alert_id: str, actor_id: str = "operator") -> dict:
        result = self.repository.update_status(alert_id, "acknowledged", actor_id=actor_id)
        self.audit_repository.log_action(category="alerts", event_type="acknowledge", payload_json=json.dumps(result), actor_id=actor_id)
        return result

    def resolve(self, alert_id: str, actor_id: str = "operator") -> dict:
        result = self.repository.update_status(alert_id, "resolved", actor_id=actor_id)
        self.audit_repository.log_action(category="alerts", event_type="resolve", payload_json=json.dumps(result), actor_id=actor_id)
        return result

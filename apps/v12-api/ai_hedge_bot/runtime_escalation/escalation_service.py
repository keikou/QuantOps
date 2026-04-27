from __future__ import annotations

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.postmortem_feedback.postmortem_service import PostmortemService
from ai_hedge_bot.runtime_escalation.models import (
    AuditEventType,
    EscalationLevel,
    EscalationRule,
    NotificationStatus,
    SourceType,
    new_id,
    normalize_severity,
    parse_json,
    severity_rank,
    stable_json,
    utc_plus_seconds_iso,
)


class RuntimeEscalationService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.postmortem = PostmortemService()

    def register_rule(
        self,
        rule_id: str,
        source_type: str,
        source_severity_min: str = "S3",
        target_escalation_level: str = "CRITICAL",
        notification_channel: str = "OPERATOR_QUEUE",
        requires_ack: bool = True,
        handoff_to_afg04: bool = True,
        cooldown_seconds: int = 900,
        dedup_key_template: str = "{source_type}:{component}:{dependency_id}:{severity}",
        enabled: bool = True,
    ) -> dict:
        rule = EscalationRule(
            rule_id=rule_id,
            source_type=SourceType(str(source_type).upper()),
            source_severity_min=normalize_severity(source_severity_min),
            target_escalation_level=EscalationLevel(str(target_escalation_level).upper()),
            notification_channel=notification_channel,
            requires_ack=bool(requires_ack),
            handoff_to_afg04=bool(handoff_to_afg04),
            cooldown_seconds=int(cooldown_seconds),
            dedup_key_template=dedup_key_template,
            enabled=bool(enabled),
        )
        self.store.append("runtime_escalation_rules", rule.to_row())
        return {"status": "ok", "rule": rule.to_row()}

    def rules(self, limit: int = 50) -> dict:
        rows = self.store.fetchall_dict("SELECT * FROM runtime_escalation_rules ORDER BY created_at DESC LIMIT ?", [max(int(limit), 1)])
        return {"status": "ok", "items": rows, "rule_summary": {"rule_count": len(rows)}}

    def evaluate_degradation(self, event_id: str) -> dict:
        row = self.store.fetchone_dict("SELECT * FROM runtime_degradation_events WHERE event_id = ? ORDER BY detected_at DESC LIMIT 1", [event_id])
        if not row:
            return {"status": "not_found", "source_event_id": event_id}
        severity = normalize_severity(row.get("severity"))
        if severity == "S4":
            source_type = SourceType.SYSTEM_HALTED
        else:
            source_type = SourceType.RUNTIME_DEGRADATION
        source = {
            "source_type": source_type.value,
            "source_event_id": event_id,
            "severity": severity,
            "component": str(row.get("component") or "system"),
            "dependency_id": "",
            "title": f"{severity} runtime degradation",
            "message": str(row.get("reason") or "runtime degradation detected"),
            "metadata": row,
        }
        return self._evaluate_source(source)

    def evaluate_dependency(self, event_id: str) -> dict:
        row = self.store.fetchone_dict("SELECT * FROM runtime_dependency_events WHERE event_id = ? ORDER BY created_at DESC LIMIT 1", [event_id])
        if not row:
            return {"status": "not_found", "source_event_id": event_id}
        event_type = str(row.get("event_type") or "")
        if event_type == "ISOLATED":
            source_type = SourceType.FALLBACK_UNAVAILABLE
        elif event_type == "RECOVERY_FAILED":
            source_type = SourceType.RECOVERY_PROBE_FAILED
        elif event_type == "CIRCUIT_OPENED":
            source_type = SourceType.CIRCUIT_OPEN_CRITICAL
        else:
            source_type = SourceType.DEPENDENCY_OUTAGE
        source = {
            "source_type": source_type.value,
            "source_event_id": event_id,
            "severity": normalize_severity(row.get("severity") or "S3"),
            "component": "dependency",
            "dependency_id": str(row.get("dependency_id") or ""),
            "title": f"{source_type.value} detected",
            "message": str(row.get("reason") or "dependency outage detected"),
            "metadata": row,
        }
        return self._evaluate_source(source)

    def latest_escalations(self, limit: int = 50) -> dict:
        rows = self.store.fetchall_dict("SELECT * FROM runtime_escalation_events ORDER BY created_at DESC LIMIT ?", [max(int(limit), 1)])
        return {"status": "ok", "items": rows, "escalation_summary": {"escalation_count": len(rows)}}

    def escalation(self, escalation_id: str) -> dict:
        row = self.store.fetchone_dict("SELECT * FROM runtime_escalation_events WHERE escalation_id = ? LIMIT 1", [escalation_id])
        notifications = self.store.fetchall_dict("SELECT * FROM runtime_operator_notifications WHERE escalation_id = ? ORDER BY created_at DESC", [escalation_id])
        handoffs = self.store.fetchall_dict("SELECT * FROM runtime_incident_handoffs WHERE escalation_id = ? ORDER BY created_at DESC", [escalation_id])
        return {"status": "ok" if row else "not_found", "escalation": row or {}, "notifications": notifications, "handoffs": handoffs}

    def notifications_latest(self, limit: int = 50) -> dict:
        rows = self.store.fetchall_dict("SELECT * FROM runtime_operator_notifications ORDER BY created_at DESC LIMIT ?", [max(int(limit), 1)])
        return {"status": "ok", "items": rows, "notification_summary": {"notification_count": len(rows)}}

    def notification(self, notification_id: str) -> dict:
        row = self.store.fetchone_dict("SELECT * FROM runtime_operator_notifications WHERE notification_id = ? ORDER BY created_at DESC LIMIT 1", [notification_id])
        acks = self.store.fetchall_dict("SELECT * FROM runtime_operator_notification_acks WHERE notification_id = ? ORDER BY created_at DESC", [notification_id])
        return {"status": "ok" if row else "not_found", "notification": row or {}, "acks": acks}

    def ack_notification(self, notification_id: str, operator_id: str = "operator.system", ack_message: str = "acknowledged") -> dict:
        notification = self.store.fetchone_dict("SELECT * FROM runtime_operator_notifications WHERE notification_id = ? ORDER BY created_at DESC LIMIT 1", [notification_id])
        if not notification:
            return {"status": "not_found", "notification_id": notification_id}
        now = utc_now_iso()
        ack = {
            "ack_id": new_id("notification_ack_"),
            "notification_id": notification_id,
            "operator_id": operator_id,
            "ack_status": "ACKED",
            "ack_message": ack_message,
            "created_at": now,
        }
        self.store.append("runtime_operator_notification_acks", ack)
        self.store.execute("UPDATE runtime_operator_notifications SET status=?, updated_at=? WHERE notification_id=?", [NotificationStatus.ACKED.value, now, notification_id])
        escalation_id = str(notification.get("escalation_id") or "")
        self._audit(escalation_id, AuditEventType.ACK_RECEIVED, "", "", "", {"notification_id": notification_id, "operator_id": operator_id})
        return {"status": "ok", "ack": ack, "notification": self.notification(notification_id).get("notification")}

    def handoffs_latest(self, limit: int = 50) -> dict:
        rows = self.store.fetchall_dict("SELECT * FROM runtime_incident_handoffs ORDER BY created_at DESC LIMIT ?", [max(int(limit), 1)])
        return {"status": "ok", "items": rows, "handoff_summary": {"handoff_count": len(rows)}}

    def handoff(self, handoff_id: str) -> dict:
        row = self.store.fetchone_dict("SELECT * FROM runtime_incident_handoffs WHERE handoff_id = ? ORDER BY created_at DESC LIMIT 1", [handoff_id])
        attempts = self.store.fetchall_dict("SELECT * FROM runtime_incident_handoff_attempts WHERE handoff_id = ? ORDER BY created_at DESC", [handoff_id])
        return {"status": "ok" if row else "not_found", "handoff": row or {}, "attempts": attempts}

    def retry_handoff(self, handoff_id: str, force_fail: bool = False) -> dict:
        handoff = self.store.fetchone_dict("SELECT * FROM runtime_incident_handoffs WHERE handoff_id = ? ORDER BY created_at DESC LIMIT 1", [handoff_id])
        if not handoff:
            return {"status": "not_found", "handoff_id": handoff_id}
        return self._ingest_handoff(handoff, force_fail=force_fail)

    def audit_latest(self, limit: int = 100) -> dict:
        rows = self.store.fetchall_dict("SELECT * FROM runtime_escalation_audit_log ORDER BY created_at DESC LIMIT ?", [max(int(limit), 1)])
        return {"status": "ok", "items": rows, "audit_summary": {"audit_count": len(rows)}}

    def _evaluate_source(self, source: dict) -> dict:
        rule = self._matching_rule(source)
        if not rule:
            return {"status": "no_rule", "source": source}
        dedup_key = self._dedup_key(rule, source)
        self._audit("", AuditEventType.RULE_EVALUATED, source["source_event_id"], str(rule["rule_id"]), dedup_key, source)
        duplicate = self._check_duplicate(rule, dedup_key)
        if duplicate:
            self._audit(str(duplicate.get("active_escalation_id") or ""), AuditEventType.DUPLICATE_SUPPRESSED, source["source_event_id"], str(rule["rule_id"]), dedup_key, duplicate)
            return {"status": "duplicate_suppressed", "dedup": duplicate, "rule": rule}
        escalation = self._create_escalation(rule, source, dedup_key)
        notification = self._create_notification(escalation, rule)
        handoff = {}
        if bool(rule.get("handoff_to_afg04")):
            handoff = self._create_handoff(escalation, source)
        return {"status": "ok", "rule": rule, "escalation": escalation, "notification": notification, "handoff": handoff}

    def _matching_rule(self, source: dict) -> dict | None:
        rows = self.store.fetchall_dict(
            "SELECT * FROM runtime_escalation_rules WHERE source_type = ? AND enabled = TRUE ORDER BY created_at ASC",
            [source["source_type"]],
        )
        for row in reversed(rows):
            if severity_rank(source.get("severity")) >= severity_rank(row.get("source_severity_min")):
                return row
        default = self._default_rule(source)
        self.store.append("runtime_escalation_rules", default)
        return default

    def _default_rule(self, source: dict) -> dict:
        severity = normalize_severity(source.get("severity"))
        level = EscalationLevel.EMERGENCY.value if severity == "S4" else EscalationLevel.CRITICAL.value
        return {
            "rule_id": f"srh03.default.{str(source['source_type']).lower()}",
            "source_type": source["source_type"],
            "source_severity_min": "S3",
            "target_escalation_level": level,
            "notification_channel": "OPERATOR_QUEUE",
            "requires_ack": True,
            "handoff_to_afg04": True,
            "cooldown_seconds": 900,
            "dedup_key_template": "{source_type}:{component}:{dependency_id}:{severity}",
            "enabled": True,
            "created_at": utc_now_iso(),
        }

    def _dedup_key(self, rule: dict, source: dict) -> str:
        template = str(rule.get("dedup_key_template") or "{source_type}:{component}:{dependency_id}:{severity}")
        return template.format(
            source_type=source.get("source_type", ""),
            source_event_id=source.get("source_event_id", ""),
            component=source.get("component", ""),
            dependency_id=source.get("dependency_id", ""),
            severity=source.get("severity", ""),
        )

    def _check_duplicate(self, rule: dict, dedup_key: str) -> dict | None:
        row = self.store.fetchone_dict("SELECT * FROM runtime_escalation_dedup WHERE dedup_key = ? ORDER BY last_seen_at DESC LIMIT 1", [dedup_key])
        if not row:
            return None
        suppressed = int(row.get("suppressed_count") or 0) + 1
        now = utc_now_iso()
        self.store.append(
            "runtime_escalation_dedup",
            {
                "dedup_id": new_id("escalation_dedup_"),
                "dedup_key": dedup_key,
                "cooldown_seconds": int(rule.get("cooldown_seconds") or 900),
                "first_seen_at": row.get("first_seen_at") or now,
                "last_seen_at": now,
                "suppressed_count": suppressed,
                "active_escalation_id": row.get("active_escalation_id") or "",
            },
        )
        return {**row, "suppressed_count": suppressed}

    def _create_escalation(self, rule: dict, source: dict, dedup_key: str) -> dict:
        now = utc_now_iso()
        escalation = {
            "escalation_id": new_id("escalation_"),
            "rule_id": rule["rule_id"],
            "source_type": source["source_type"],
            "source_event_id": source["source_event_id"],
            "source_severity": source["severity"],
            "level": rule["target_escalation_level"],
            "status": "OPEN",
            "dedup_key": dedup_key,
            "title": source["title"],
            "message": source["message"],
            "created_at": now,
            "metadata_json": stable_json(source.get("metadata") or {}),
        }
        self.store.append("runtime_escalation_events", escalation)
        self.store.append(
            "runtime_escalation_dedup",
            {
                "dedup_id": new_id("escalation_dedup_"),
                "dedup_key": dedup_key,
                "cooldown_seconds": int(rule.get("cooldown_seconds") or 900),
                "first_seen_at": now,
                "last_seen_at": now,
                "suppressed_count": 0,
                "active_escalation_id": escalation["escalation_id"],
            },
        )
        self._audit(escalation["escalation_id"], AuditEventType.ESCALATION_CREATED, source["source_event_id"], str(rule["rule_id"]), dedup_key, escalation)
        return escalation

    def _create_notification(self, escalation: dict, rule: dict) -> dict:
        now = utc_now_iso()
        requires_ack = bool(rule.get("requires_ack")) or escalation.get("level") in {EscalationLevel.CRITICAL.value, EscalationLevel.EMERGENCY.value}
        notification = {
            "notification_id": new_id("notification_"),
            "escalation_id": escalation["escalation_id"],
            "level": escalation["level"],
            "channel": rule.get("notification_channel") or "OPERATOR_QUEUE",
            "title": escalation["title"],
            "message": escalation["message"],
            "requires_ack": requires_ack,
            "ack_deadline_at": utc_plus_seconds_iso(900 if escalation.get("level") == "CRITICAL" else 300) if requires_ack else None,
            "status": NotificationStatus.ACK_REQUIRED.value if requires_ack else NotificationStatus.DELIVERED.value,
            "created_at": now,
            "updated_at": now,
        }
        delivery = {
            "delivery_id": new_id("notification_delivery_"),
            "notification_id": notification["notification_id"],
            "channel": notification["channel"],
            "delivery_status": "DELIVERED",
            "detail": "queued_for_operator",
            "created_at": now,
        }
        self.store.append("runtime_operator_notifications", notification)
        self.store.append("runtime_operator_notification_delivery", delivery)
        self._audit(escalation["escalation_id"], AuditEventType.NOTIFICATION_CREATED, escalation["source_event_id"], escalation["rule_id"], escalation["dedup_key"], notification)
        return notification

    def _create_handoff(self, escalation: dict, source: dict) -> dict:
        now = utc_now_iso()
        handoff = {
            "handoff_id": new_id("incident_handoff_"),
            "escalation_id": escalation["escalation_id"],
            "source_system": "SRH",
            "source_packet": "SRH-03",
            "incident_type": self._incident_type(source),
            "severity": escalation["source_severity"],
            "title": escalation["title"],
            "summary": escalation["message"],
            "source_refs_json": stable_json({"source_event_id": escalation["source_event_id"], "source_type": escalation["source_type"]}),
            "status": "PENDING_INGEST",
            "incident_id": "",
            "created_at": now,
            "updated_at": now,
        }
        self.store.append("runtime_incident_handoffs", handoff)
        self._audit(escalation["escalation_id"], AuditEventType.HANDOFF_CREATED, escalation["source_event_id"], escalation["rule_id"], escalation["dedup_key"], handoff)
        return self._ingest_handoff(handoff)

    def _ingest_handoff(self, handoff: dict, force_fail: bool = False) -> dict:
        now = utc_now_iso()
        if force_fail:
            attempt = {"attempt_id": new_id("handoff_attempt_"), "handoff_id": handoff["handoff_id"], "attempt_status": "FAILED", "detail": "forced_failure", "created_at": now}
            self.store.append("runtime_incident_handoff_attempts", attempt)
            self.store.execute("UPDATE runtime_incident_handoffs SET status=?, updated_at=? WHERE handoff_id=?", ["FAILED", now, handoff["handoff_id"]])
            self._audit(str(handoff.get("escalation_id") or ""), AuditEventType.HANDOFF_FAILED, "", "", "", attempt)
            return {"status": "failed", "handoff": {**handoff, "status": "FAILED"}, "attempt": attempt}
        incident = self.postmortem.ingest(
            source_system="SRH",
            source_event_id=str(handoff["escalation_id"]),
            severity=str(handoff.get("severity") or "S3"),
            incident_type=str(handoff.get("incident_type") or "runtime"),
            affected_scope="runtime",
            target_id=str(handoff.get("escalation_id") or ""),
            summary=str(handoff.get("summary") or handoff.get("title") or "runtime escalation"),
            evidence_json=handoff.get("source_refs_json") or "{}",
        ).get("incident", {})
        status = "INGESTED" if incident else "FAILED"
        attempt = {
            "attempt_id": new_id("handoff_attempt_"),
            "handoff_id": handoff["handoff_id"],
            "attempt_status": status,
            "detail": str(incident.get("incident_id") or "incident_ingest_failed"),
            "created_at": now,
        }
        self.store.append("runtime_incident_handoff_attempts", attempt)
        self.store.execute("UPDATE runtime_incident_handoffs SET status=?, incident_id=?, updated_at=? WHERE handoff_id=?", [status, incident.get("incident_id", ""), now, handoff["handoff_id"]])
        self._audit(str(handoff.get("escalation_id") or ""), AuditEventType.HANDOFF_INGESTED if incident else AuditEventType.HANDOFF_FAILED, "", "", "", attempt)
        return {"status": "ok" if incident else "failed", "handoff": self.handoff(str(handoff["handoff_id"])).get("handoff"), "attempt": attempt, "incident": incident}

    def _incident_type(self, source: dict) -> str:
        mapping = {
            SourceType.RUNTIME_DEGRADATION.value: "RUNTIME_DEGRADATION",
            SourceType.SAFE_MODE_TRIGGERED.value: "RUNTIME_SAFE_MODE",
            SourceType.SYSTEM_HALTED.value: "RUNTIME_HALT",
            SourceType.DEPENDENCY_OUTAGE.value: "RUNTIME_DEPENDENCY_OUTAGE",
            SourceType.CIRCUIT_OPEN_CRITICAL.value: "RUNTIME_DEPENDENCY_OUTAGE",
            SourceType.FALLBACK_UNAVAILABLE.value: "RUNTIME_FALLBACK_FAILURE",
            SourceType.RECOVERY_PROBE_FAILED.value: "RUNTIME_RECOVERY_FAILURE",
        }
        return mapping.get(str(source.get("source_type") or ""), "RUNTIME_ESCALATION")

    def _audit(self, escalation_id: str, event_type: AuditEventType, source_event_id: str, rule_id: str, dedup_key: str, details: dict) -> dict:
        row = {
            "audit_id": new_id("escalation_audit_"),
            "escalation_id": escalation_id,
            "event_type": event_type.value,
            "source_event_id": source_event_id,
            "rule_id": rule_id,
            "dedup_key": dedup_key,
            "details_json": stable_json(details),
            "created_at": utc_now_iso(),
        }
        self.store.append("runtime_escalation_audit_log", row)
        return row

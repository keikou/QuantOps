from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
from typing import Any

from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_run_id


SCHEMA_VERSION = "afg.audit.bundle.v1"


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def canonical_timestamp(value: Any) -> str:
    if isinstance(value, datetime):
        return value.replace(tzinfo=None).isoformat(timespec="seconds")
    text = str(value or "")
    text = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text).replace(tzinfo=None).isoformat(timespec="seconds")
    except Exception:
        return text


def parse_json(value: Any, default: Any = None) -> Any:
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value))
    except Exception:
        return default


@dataclass(frozen=True)
class AuditEvidenceBundle:
    bundle_id: str
    incident_id: str
    created_at: str
    schema_version: str
    previous_hash: str
    components: dict[str, Any]
    content_hash: str
    chain_hash: str

    @staticmethod
    def build(incident_id: str, components: dict[str, Any], previous_hash: str = "", schema_version: str = SCHEMA_VERSION) -> "AuditEvidenceBundle":
        bundle_id = new_run_id().replace("run_", "audit_bundle_", 1)
        created_at = utc_now_iso()
        content_payload = {
            "bundle_id": bundle_id,
            "incident_id": incident_id,
            "created_at": canonical_timestamp(created_at),
            "schema_version": schema_version,
            "components": components,
        }
        content_hash = sha256_json(content_payload)
        chain_hash = sha256_json({"previous_hash": previous_hash, "content_hash": content_hash})
        return AuditEvidenceBundle(
            bundle_id=bundle_id,
            incident_id=incident_id,
            created_at=created_at,
            schema_version=schema_version,
            previous_hash=previous_hash,
            components=components,
            content_hash=content_hash,
            chain_hash=chain_hash,
        )

    def to_row(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "incident_id": self.incident_id,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "previous_hash": self.previous_hash,
            "content_json": stable_json(self.components),
            "content_hash": self.content_hash,
            "chain_hash": self.chain_hash,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.to_row(), "components": self.components}


@dataclass
class ReplayResult:
    replay_id: str
    incident_id: str
    bundle_id: str
    status: str
    started_at: str
    completed_at: str
    decision_trace: list[dict[str, Any]] = field(default_factory=list)
    approval_trace: list[dict[str, Any]] = field(default_factory=list)
    feedback_trace: list[dict[str, Any]] = field(default_factory=list)
    dispatch_trace: list[dict[str, Any]] = field(default_factory=list)
    validation_errors: list[str] = field(default_factory=list)

    def to_row(self) -> dict[str, Any]:
        return {
            "replay_id": self.replay_id,
            "incident_id": self.incident_id,
            "bundle_id": self.bundle_id,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "validation_errors_json": stable_json(self.validation_errors),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.to_row(),
            "decision_trace": self.decision_trace,
            "approval_trace": self.approval_trace,
            "feedback_trace": self.feedback_trace,
            "dispatch_trace": self.dispatch_trace,
            "validation_errors": self.validation_errors,
        }

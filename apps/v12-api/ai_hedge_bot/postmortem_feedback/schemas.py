from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any


class IncidentSeverity(str, Enum):
    S1 = "S1"
    S2 = "S2"
    S3 = "S3"
    S4 = "S4"


class IncidentLifecycle(str, Enum):
    DETECTED = "DETECTED"
    TRIAGED = "TRIAGED"
    ASSIGNED = "ASSIGNED"
    REVIEWED = "REVIEWED"
    RCA_COMPLETE = "RCA_COMPLETE"
    ACTION_DEFINED = "ACTION_DEFINED"
    APPROVED = "APPROVED"
    CLOSED = "CLOSED"
    FEEDBACK_EMITTED = "FEEDBACK_EMITTED"


class FeedbackTarget(str, Enum):
    AES = "AES"
    ORC = "ORC"
    AFG_POLICY = "AFG_POLICY"
    LCC = "LCC"
    EXECUTION = "EXECUTION"


class FeedbackType(str, Enum):
    THRESHOLD_TIGHTEN = "threshold_tighten"
    THRESHOLD_LOOSEN = "threshold_loosen"
    DETECTOR_RULE_ADD = "detector_rule_add"
    POLICY_RULE_ADD = "policy_rule_add"
    POLICY_RULE_TIGHTEN = "policy_rule_tighten"
    OVERRIDE_LIMIT_TIGHTEN = "override_limit_tighten"
    ALPHA_FAMILY_PENALTY = "alpha_family_penalty"
    KILL_SWITCH_TIGHTEN = "kill_switch_tighten"
    CAPITAL_CAP_TIGHTEN = "capital_cap_tighten"
    VENUE_BLOCK_RULE = "venue_block_rule"
    BROKER_HEALTH_RULE = "broker_health_rule"


SEVERITY_RANK = {"S4": 1, "S3": 2, "S2": 3, "S1": 4}
HIGH_SEVERITIES = {"S1", "S2"}


@dataclass(frozen=True)
class PostmortemFeedback:
    feedback_id: str
    incident_id: str
    rca_id: str
    target_system: str
    feedback_type: str
    severity: str
    confidence: float
    payload: dict[str, Any]
    requires_approval: bool
    approved: bool
    created_at: str

    def to_row(self) -> dict[str, Any]:
        return {
            "feedback_id": self.feedback_id,
            "incident_id": self.incident_id,
            "rca_id": self.rca_id,
            "target_system": self.target_system,
            "feedback_type": self.feedback_type,
            "severity": self.severity,
            "confidence": self.confidence,
            "payload_json": to_json(self.payload),
            "requires_approval": self.requires_approval,
            "approved": self.approved,
            "applied": False,
            "created_at": self.created_at,
            "approved_at": None,
            "applied_at": None,
        }


def normalize_severity(value: str | None) -> str:
    raw = str(value or "S3").upper()
    aliases = {
        "CRITICAL": "S1",
        "CATASTROPHIC": "S1",
        "L5_GLOBAL_HALT": "S1",
        "HIGH": "S2",
        "MAJOR": "S2",
        "L4_PARTIAL_HALT": "S2",
        "MEDIUM": "S3",
        "MODERATE": "S3",
        "L3_FREEZE": "S3",
        "LOW": "S4",
        "MINOR": "S4",
        "L1_WATCH": "S4",
        "L2_REDUCE": "S4",
    }
    return raw if raw in SEVERITY_RANK else aliases.get(raw, "S3")


def severity_to_risk_level(severity: str) -> str:
    return {
        "S1": "CRITICAL",
        "S2": "HIGH",
        "S3": "MEDIUM",
        "S4": "LOW",
    }.get(normalize_severity(severity), "MEDIUM")


def parse_json(value: Any, default: Any = None) -> Any:
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value))
    except Exception:
        return default


def to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def stable_hash(value: Any) -> str:
    payload = to_json(value)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def stable_feedback_id(incident_id: str, rca_id: str, target_system: str, feedback_type: str, payload: dict[str, Any]) -> str:
    digest = stable_hash(
        {
            "incident_id": incident_id,
            "rca_id": rca_id,
            "target_system": target_system,
            "feedback_type": feedback_type,
            "payload": payload,
        }
    )
    return f"pmfb_{digest}"


def dispatch_idempotency_key(feedback: dict[str, Any]) -> str:
    return ":".join(
        [
            str(feedback.get("feedback_id") or ""),
            str(feedback.get("target_system") or ""),
            str(feedback.get("feedback_type") or ""),
        ]
    )


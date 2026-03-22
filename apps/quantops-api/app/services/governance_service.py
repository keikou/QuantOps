from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def _safe_list(value: Any) -> List[Dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        return [value]
    return []


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


class GovernanceService:
    def __init__(self, base_url: str, timeout_seconds: int = 10) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def _get_json(self, path: str) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        with httpx.Client(timeout=self.timeout_seconds) as client:
            resp = client.get(url)
            resp.raise_for_status()
            payload = resp.json()
            if isinstance(payload, dict):
                payload["_endpoint"] = path
                return payload
            return {"status": "ok", "data": payload, "_endpoint": path}

    def _safe_call(self, path: str) -> Dict[str, Any]:
        try:
            return self._get_json(path)
        except Exception as exc:  # noqa: BLE001
            return {
                "status": "error",
                "error": str(exc),
                "_endpoint": path,
            }

    def get_overview(self) -> Dict[str, Any]:
        overview = self._safe_call("/research-factory/governance-overview")
        live_review_payload = self._safe_call("/research-factory/live-review")
        decay_payload = self._safe_call("/research-factory/alpha-decay")

        promotions = _safe_list(overview.get("promotions"))
        live_reviews = _safe_list(overview.get("live_reviews"))
        decay_events = _safe_list(overview.get("decay_events"))
        rollback_events = _safe_list(overview.get("rollback_events"))
        champion_challenger_runs = _safe_list(overview.get("champion_challenger_runs"))

        # Fallback to single-object endpoints if list fields are absent/empty.
        live_review_obj = _safe_dict(live_review_payload.get("review"))
        decay_obj = _safe_dict(decay_payload.get("decay"))

        if not live_reviews and live_review_obj:
            live_reviews = [live_review_obj]
        if not decay_events and decay_obj:
            decay_events = [decay_obj]

        latest_promotion = _safe_dict(
            overview.get("latest_promotion") or (promotions[0] if promotions else {})
        )
        latest_live_review = _safe_dict(
            overview.get("latest_live_review") or live_review_obj or (live_reviews[0] if live_reviews else {})
        )
        latest_decay = _safe_dict(
            overview.get("latest_decay") or decay_obj or (decay_events[0] if decay_events else {})
        )
        latest_rollback = _safe_dict(
            overview.get("latest_rollback") or (rollback_events[0] if rollback_events else {})
        )
        latest_champion_challenger = _safe_dict(
            overview.get("latest_champion_challenger")
            or (champion_challenger_runs[0] if champion_challenger_runs else {})
        )

        return {
            "status": "ok",
            "as_of": _now_iso(),
            "summary": {
                "promotion_decisions": _safe_dict(overview.get("promotion_decisions")),
                "live_review_decisions": _safe_dict(overview.get("live_review_decisions")),
                "decay_severity": _safe_dict(overview.get("decay_severity")),
            },
            "latest": {
                "promotion": latest_promotion,
                "live_review": latest_live_review,
                "decay": latest_decay,
                "rollback": latest_rollback,
                "champion_challenger": latest_champion_challenger,
            },
            "lists": {
                "promotion_candidates": promotions,
                "live_reviews": live_reviews,
                "decay_alerts": decay_events,
                "rollback_candidates": rollback_events,
                "champion_challenger_runs": champion_challenger_runs,
            },
            "meta": {
                "source": "quantops",
                "upstream_endpoint": "/research-factory/governance-overview",
                "upstream_status": overview.get("status", "unknown"),
                "upstream": {
                    "governance_overview": {
                        "status": overview.get("status"),
                        "endpoint": overview.get("_endpoint"),
                    },
                    "live_review": {
                        "status": live_review_payload.get("status"),
                        "endpoint": live_review_payload.get("_endpoint"),
                    },
                    "alpha_decay": {
                        "status": decay_payload.get("status"),
                        "endpoint": decay_payload.get("_endpoint"),
                    },
                },
            },
        }

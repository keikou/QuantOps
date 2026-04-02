from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.services.runtime.runtime_service import RuntimeService


class RecoveryReplayDiagnosticBundleService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.runtime_service = RuntimeService()

    @staticmethod
    def _decode(raw: object) -> dict[str, Any]:
        if isinstance(raw, dict):
            return dict(raw)
        try:
            return json.loads(str(raw or "{}"))
        except Exception:
            return {}

    @staticmethod
    def _snapshot_age_sec(value: object) -> float | None:
        if value in (None, ""):
            return None
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return round(max(0.0, (datetime.now(timezone.utc) - dt).total_seconds()), 3)
        except Exception:
            return None

    def build(self) -> dict[str, Any]:
        order = self.store.fetchone_dict(
            """
            SELECT live_order_id, created_at, updated_at, symbol, side, qty, venue, order_type, tif, decision_id, status, venue_order_id, metadata_json
            FROM live_orders
            ORDER BY updated_at DESC, created_at DESC
            LIMIT 1
            """
        )
        if not order:
            return {
                "status": "no_data",
                "live_order_id": None,
                "operator_message": "No live recovery or replay evidence is available yet.",
                "consistency": {"status": "no_data", "operator_ready": False, "mismatches": ["missing_live_order"]},
            }

        order_payload = dict(order)
        order_payload["metadata"] = self._decode(order_payload.pop("metadata_json", None))

        fill_row = self.store.fetchone_dict(
            """
            SELECT live_fill_id, created_at, live_order_id, venue_order_id, symbol, side, fill_qty, fill_price, status, metadata_json
            FROM live_fills
            WHERE live_order_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [order["live_order_id"]],
        )
        fill_payload = dict(fill_row or {})
        fill_payload["metadata"] = self._decode(fill_payload.pop("metadata_json", None))

        event_rows = self.store.fetchall_dict(
            """
            SELECT reconciliation_event_id, created_at, live_order_id, venue_order_id, event_type, status, matched, details_json
            FROM live_reconciliation_events
            WHERE live_order_id = ?
            ORDER BY created_at ASC
            """,
            [order["live_order_id"]],
        )
        events: list[dict[str, Any]] = []
        for row in event_rows:
            item = dict(row)
            item["details"] = self._decode(item.pop("details_json", None))
            events.append(item)

        incident_row = self.store.fetchone_dict(
            """
            SELECT incident_id, created_at, category, severity, status, summary, details_json
            FROM live_incidents
            WHERE details_json LIKE ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [f'%{order["live_order_id"]}%'],
        )
        incident = dict(incident_row or {})
        incident["details"] = self._decode(incident.pop("details_json", None))

        audit_rows = self.store.fetchall_dict(
            """
            SELECT category, event_type, actor, created_at
            FROM audit_logs
            WHERE category = 'runtime'
            ORDER BY created_at ASC
            """
        )
        source_path = (
            str((fill_payload.get("metadata") or {}).get("source") or "")
            or str(next((item.get("details", {}).get("source") for item in events if item.get("details", {}).get("source")), "") or "")
            or None
        )
        event_types = [str(item.get("event_type") or "") for item in events]
        recovery_resolved = "recovery_resolved" in event_types
        mismatch_detected = "fill_mismatch" in event_types
        final_trading_state = str(self.runtime_service.get_trading_state().get("trading_state") or "running").lower()

        mismatches: list[str] = []
        if not mismatch_detected:
            mismatches.append("missing_fill_mismatch_event")
        if not recovery_resolved:
            mismatches.append("missing_recovery_resolved_event")
        if str(order.get("status") or "") != "mismatch":
            mismatches.append("unexpected_final_order_status")
        if final_trading_state != "running":
            mismatches.append("trading_state_not_recovered")
        if str(incident.get("status") or "") != "resolved":
            mismatches.append("incident_not_resolved")
        if source_path not in {"ingest", "replay"}:
            mismatches.append("missing_reconciliation_source")

        source_snapshot_time = (
            fill_payload.get("created_at")
            or incident.get("created_at")
            or order.get("updated_at")
            or order.get("created_at")
        )

        parity_summary = {
            "source_path": source_path,
            "order_status": order.get("status"),
            "incident_status": incident.get("status"),
            "trading_state": final_trading_state,
            "event_types": event_types,
            "mismatch_detected": mismatch_detected,
            "recovery_resolved": recovery_resolved,
        }

        return {
            "status": "ok",
            "live_order_id": order.get("live_order_id"),
            "venue_order_id": order.get("venue_order_id"),
            "source_snapshot_time": source_snapshot_time,
            "data_freshness_sec": self._snapshot_age_sec(source_snapshot_time),
            "order": order_payload,
            "latest_fill": fill_payload,
            "reconciliation_events": events,
            "incident": incident,
            "runtime_audit_chain": audit_rows,
            "recovery_summary": {
                "source_path": source_path,
                "order_status": order.get("status"),
                "incident_status": incident.get("status"),
                "trading_state": final_trading_state,
                "operator_message": "Recovery and replay evidence are coherent for the latest live reconciliation chain." if not mismatches else "Recovery or replay evidence is incomplete for the latest live reconciliation chain.",
            },
            "parity_summary": parity_summary,
            "consistency": {
                "status": "ok" if not mismatches else "warn",
                "operator_ready": not mismatches,
                "mismatches": mismatches,
            },
        }

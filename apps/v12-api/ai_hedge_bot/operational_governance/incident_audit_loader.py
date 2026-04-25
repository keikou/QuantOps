from __future__ import annotations


class IncidentAuditLoader:
    def __init__(self, store) -> None:
        self.store = store

    def load(self, limit: int = 200) -> list[dict]:
        incidents: list[dict] = []
        incidents.extend(self._operational(limit))
        incidents.extend(self._execution(limit))
        incidents.extend(self._data(limit))
        return incidents[: max(int(limit), 1)]

    def _operational(self, limit: int) -> list[dict]:
        rows = self.store.fetchall_dict("SELECT * FROM operational_incidents ORDER BY created_at DESC LIMIT ?", [limit])
        return [
            {
                "source_incident_id": row.get("incident_id"),
                "source_system": "ORC-01",
                "incident_type": row.get("incident_type"),
                "risk_level": row.get("risk_level"),
                "affected_scope": row.get("domain"),
                "target_id": row.get("affected_entities"),
                "recommended_action": row.get("recommended_action"),
                "summary": row.get("summary"),
                "created_at": row.get("created_at"),
            }
            for row in rows
        ]

    def _execution(self, limit: int) -> list[dict]:
        rows = self.store.fetchall_dict("SELECT * FROM execution_incidents ORDER BY created_at DESC LIMIT ?", [limit])
        return [
            {
                "source_incident_id": row.get("incident_id"),
                "source_system": "ORC-03",
                "incident_type": row.get("incident_type"),
                "risk_level": row.get("risk_level"),
                "affected_scope": "execution",
                "target_id": ":".join(part for part in [str(row.get("broker_id") or ""), str(row.get("venue_id") or "")] if part),
                "recommended_action": row.get("recommended_action"),
                "summary": row.get("summary"),
                "created_at": row.get("created_at"),
            }
            for row in rows
        ]

    def _data(self, limit: int) -> list[dict]:
        rows = self.store.fetchall_dict("SELECT * FROM data_incidents ORDER BY created_at DESC LIMIT ?", [limit])
        return [
            {
                "source_incident_id": row.get("incident_id"),
                "source_system": "ORC-04",
                "incident_type": row.get("incident_type"),
                "risk_level": row.get("risk_level"),
                "affected_scope": row.get("affected_scope"),
                "target_id": row.get("affected_entities"),
                "recommended_action": row.get("recommended_action"),
                "summary": row.get("summary"),
                "created_at": row.get("created_at"),
            }
            for row in rows
        ]


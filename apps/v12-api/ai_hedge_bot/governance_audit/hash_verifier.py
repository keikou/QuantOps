from __future__ import annotations

from ai_hedge_bot.governance_audit.models import canonical_timestamp, parse_json, sha256_json


class HashVerifier:
    def verify_bundle_row(self, row: dict) -> tuple[bool, list[str]]:
        errors: list[str] = []
        components = parse_json(row.get("content_json"), {})
        content_payload = {
            "bundle_id": row.get("bundle_id"),
            "incident_id": row.get("incident_id"),
            "created_at": canonical_timestamp(row.get("created_at")),
            "schema_version": row.get("schema_version"),
            "components": components,
        }
        expected_content_hash = sha256_json(content_payload)
        if expected_content_hash != row.get("content_hash"):
            errors.append("content_hash_mismatch")
        expected_chain_hash = sha256_json({"previous_hash": row.get("previous_hash") or "", "content_hash": row.get("content_hash")})
        if expected_chain_hash != row.get("chain_hash"):
            errors.append("chain_hash_mismatch")
        return len(errors) == 0, errors

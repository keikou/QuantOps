# AFG-05 Audit Evidence Bundle Design

## Purpose

Fix every governance decision as auditable evidence.

## Evidence Types

```text
- incident evidence
- RCA evidence
- approval evidence
- action item evidence
- feedback evidence
- dispatch evidence
- policy proposal evidence
```

## Schema

```json
{
  "bundle_id": "",
  "incident_id": "",
  "schema_version": "afg.audit.bundle.v1",
  "created_at": "",
  "previous_hash": "",
  "content_hash": "",
  "chain_hash": "",
  "components": {
    "incident": {},
    "reviews": [],
    "rca": [],
    "approvals": [],
    "action_items": [],
    "feedback": [],
    "dispatch": []
  }
}
```

## Hash Strategy

```text
- SHA256 over stable JSON
- content_hash covers bundle identity, timestamp, schema version, and components
- chain_hash covers previous_hash and content_hash
```

## Storage

```text
- append-only runtime table
- immutable JSON export
- export index table
```

## Validation

```text
- content hash match
- chain hash match
- incident evidence present
- RCA evidence present
- approval evidence present when feedback requires approval
- event order trace can be reconstructed
```


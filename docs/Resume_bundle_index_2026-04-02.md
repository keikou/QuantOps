# Resume Bundle Index 2026-04-02

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `System Reliability Hardening Track`
Status: `active_index`

## Primary Entry Points

Read in this order:

1. `docs/Auto_resume_handover_2026-04-02.md`
2. `docs/Resume_operator_packet_latest.md`
3. `docs/Hardening_architect_handoff_latest.md`
4. `runtime/snapshots/hardening_evidence_latest.json`

Primary live API entrypoint:

```text
GET /system/hardening-handover-manifest
```

## Live Surfaces

- `GET /system/hardening-handover-manifest`
- `GET /system/hardening-status`
- `GET /system/operator-diagnostic-bundle`
- `GET /system/recovery-replay-diagnostic-bundle`
- `GET /system/hardening-evidence-snapshot/latest`
- `GET /system/hardening-architect-handoff/latest`
- `GET /system/resume-operator-packet/latest`

## Saved Artifacts

- `docs/Auto_resume_handover_2026-04-02.md`
- `docs/Resume_operator_packet_latest.md`
- `docs/Hardening_architect_handoff_latest.md`
- `runtime/snapshots/hardening_evidence_latest.json`

## Recommended Verification Set

- `python test_bundle/scripts/verify_hardening_status_surface.py --json`
- `python test_bundle/scripts/verify_hardening_evidence_snapshot.py --json`
- `python test_bundle/scripts/verify_hardening_architect_handoff.py --json`
- `python test_bundle/scripts/verify_hardening_handover_manifest.py --json`
- `python test_bundle/scripts/verify_resume_automation_helper.py --json`
- `python test_bundle/scripts/verify_resume_operator_packet.py --json`

Expected shape:

- `status = ok`
- `failures = []`

## One-Command Helpers

- `python test_bundle/scripts/run_resume_quickcheck.py --json`
- `python test_bundle/scripts/run_resume_bundle_refresh.py --json`
- `python test_bundle/scripts/resume_hardening_helper.py --json`

Suggested order:

1. quickcheck
2. refresh
3. helper summary

## Meaning

This index is the shortest human-facing route through the current hardening resume bundle.
It does not replace the manifest; it points humans to the same artifact set that the manifest exposes for machines.

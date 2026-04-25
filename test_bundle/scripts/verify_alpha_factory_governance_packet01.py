from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Alpha_factory_governance_operator_control_packet01_plan.md"
TASK_DOC = REPO_ROOT / "docs" / "04_tasks" / "afg01_alpha_factory_operator_control_plane_2026-04-25.md"
CONTRACT_DOC = REPO_ROOT / "docs" / "07_interfaces" / "afg_operator_control_contracts.md"


def _contains(path: Path, needles: list[str], failures: list[str], prefix: str) -> None:
    if not path.exists():
        failures.append(f"missing:{path.name}")
        return
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            failures.append(f"{prefix}:{needle}")


def main() -> None:
    failures: list[str] = []
    needles = [
        "/system/operator-action/submit",
        "/system/operator-actions/latest",
        "/system/pending-approvals/latest",
        "/system/pending-approvals/{approval_id}",
        "/system/pending-approvals/{approval_id}/approve",
        "/system/pending-approvals/{approval_id}/reject",
        "/system/operator-override",
        "/system/operator-overrides/latest",
        "/system/operator-overrides/{override_id}/expire",
        "/system/audit-log/latest",
        "/system/governance-state/latest",
        "/system/governance/sync",
        "/system/governance/dispatch",
        "/system/governance/dispatch/latest",
    ]
    _contains(PLAN_DOC, needles, failures, "plan_missing")
    _contains(TASK_DOC, needles, failures, "task_missing")
    _contains(CONTRACT_DOC, needles, failures, "contract_missing")
    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

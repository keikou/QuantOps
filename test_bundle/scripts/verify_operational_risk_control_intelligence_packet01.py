from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Operational_risk_control_intelligence_packet01_plan.md"
TASK_DOC = REPO_ROOT / "docs" / "04_tasks" / "orc01_operational_risk_control_plane_2026-04-25.md"
CONTRACT_DOC = REPO_ROOT / "docs" / "07_interfaces" / "orc_operational_risk_contracts.md"


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
        "/system/operational-risk/run",
        "/system/risk-state/latest",
        "/system/global-risk-metrics/latest",
        "/system/anomaly-detection/latest",
        "/system/operational-incidents/latest",
        "/system/risk-response/latest",
        "/system/risk-response/execute",
        "/system/global-kill-switch",
        "/system/global-kill-switch/latest",
        "/system/operational-risk/override",
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


from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

FILES = {
    "current_task": REPO_ROOT / "docs" / "04_tasks" / "current.md",
    "active_tasks": REPO_ROOT / "docs" / "04_tasks" / "active_tasks.md",
    "task_template": REPO_ROOT / "docs" / "04_tasks" / "task_template.md",
    "workflow_index": REPO_ROOT / "docs" / "05_workflows" / "README.md",
    "dev_flow": REPO_ROOT / "docs" / "05_workflows" / "dev-flow.md",
    "incident_flow": REPO_ROOT / "docs" / "05_workflows" / "incident-flow.md",
    "runtime_acceptance_flow": REPO_ROOT / "docs" / "05_workflows" / "runtime-acceptance-flow.md",
}


def expect(text: str, needle: str, failures: list[str], label: str) -> None:
    if needle not in text:
        failures.append(f"{label}_missing:{needle}")


def main() -> None:
    failures: list[str] = []

    for label, path in FILES.items():
        if not path.exists():
            failures.append(f"missing:{label}")

    if FILES["current_task"].exists():
        text = FILES["current_task"].read_text(encoding="utf-8")
        for needle in [
            "Execution Reality",
            "do not restart `Cross-Phase Acceptance`",
            "next lane beyond the completed hardening/resume slice",
        ]:
            expect(text, needle, failures, "current_task")

    if FILES["workflow_index"].exists():
        text = FILES["workflow_index"].read_text(encoding="utf-8")
        for needle in [
            "dev-flow.md",
            "incident-flow.md",
            "runtime-acceptance-flow.md",
        ]:
            expect(text, needle, failures, "workflow_index")

    if FILES["incident_flow"].exists():
        text = FILES["incident_flow"].read_text(encoding="utf-8")
        for needle in [
            "A stale conversation recommendation is not a regression.",
            "failed verifier",
        ]:
            expect(text, needle, failures, "incident_flow")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

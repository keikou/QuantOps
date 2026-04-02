from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_DOC = REPO_ROOT / "docs" / "00_index" / "README.md"
MAP_DOC = REPO_ROOT / "docs" / "00_index" / "current_docs_migration_map.md"


def require_contains(text: str, needle: str, failures: list[str], label: str) -> None:
    if needle not in text:
        failures.append(f"{label}_missing:{needle}")


def main() -> None:
    failures: list[str] = []

    if not INDEX_DOC.exists():
        failures.append("missing_index_doc")
    if not MAP_DOC.exists():
        failures.append("missing_map_doc")

    if INDEX_DOC.exists():
        text = INDEX_DOC.read_text(encoding="utf-8")
        for needle in [
            "Docs Operating Index",
            "Target Structure",
            "AI Agent Entry",
            "Human Entry",
            "Execution Reality",
            "current_docs_migration_map.md",
        ]:
            require_contains(text, needle, failures, "index")

    if MAP_DOC.exists():
        text = MAP_DOC.read_text(encoding="utf-8")
        for needle in [
            "## 00_index",
            "## 03_plans",
            "## 04_tasks",
            "## 05_workflows",
            "## 07_interfaces",
            "## 11_reports",
            "Cross_phase_acceptance_plan.md",
            "Post_Phase7_hardening_architect_report_2026-04-02.md",
        ]:
            require_contains(text, needle, failures, "map")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

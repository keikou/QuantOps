from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

FILES = {
    "context_index": REPO_ROOT / "docs" / "01_context" / "README.md",
    "project_state": REPO_ROOT / "docs" / "01_context" / "project_state.md",
    "working_assumptions": REPO_ROOT / "docs" / "01_context" / "working_assumptions.md",
    "migration_map": REPO_ROOT / "docs" / "00_index" / "current_docs_migration_map.md",
}


def expect(text: str, needle: str, failures: list[str], label: str) -> None:
    if needle not in text:
        failures.append(f"{label}_missing:{needle}")


def main() -> None:
    failures: list[str] = []

    for label, path in FILES.items():
        if not path.exists():
            failures.append(f"missing:{label}")

    if FILES["context_index"].exists():
        text = FILES["context_index"].read_text(encoding="utf-8")
        for needle in [
            "Current Canonical Files",
            "project_state.md",
            "working_assumptions.md",
            "Phase1` through `Phase7` remain complete",
            "Execution Reality",
        ]:
            expect(text, needle, failures, "context_index")

    if FILES["project_state"].exists():
        text = FILES["project_state"].read_text(encoding="utf-8")
        for needle in [
            "three-layer local trading operations stack",
            "System Reliability Hardening Track",
            "Execution Reality",
        ]:
            expect(text, needle, failures, "project_state")

    if FILES["working_assumptions"].exists():
        text = FILES["working_assumptions"].read_text(encoding="utf-8")
        for needle in [
            "do not rename the current track to `Phase8`",
            "the current hardening/resume slice is already treated as sufficiently complete",
            "a stale recommendation in a chat is not a repo regression",
        ]:
            expect(text, needle, failures, "working_assumptions")

    if FILES["migration_map"].exists():
        text = FILES["migration_map"].read_text(encoding="utf-8")
        for needle in [
            "01_context/README.md",
            "01_context/project_state.md",
            "01_context/working_assumptions.md",
        ]:
            expect(text, needle, failures, "migration_map")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

FILES = {
    "plans_index": REPO_ROOT / "docs" / "03_plans" / "README.md",
    "current_plan": REPO_ROOT / "docs" / "03_plans" / "current.md",
    "roadmap": REPO_ROOT / "docs" / "03_plans" / "roadmap.md",
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

    if FILES["plans_index"].exists():
        text = FILES["plans_index"].read_text(encoding="utf-8")
        for needle in [
            "Current Canonical Files",
            "current.md",
            "roadmap.md",
            "Execution Reality",
        ]:
            expect(text, needle, failures, "plans_index")

    if FILES["current_plan"].exists():
        text = FILES["current_plan"].read_text(encoding="utf-8")
        for needle in [
            "The current hardening/resume slice is treated as sufficiently complete.",
            "Execution Reality",
            "another hardening-only lane",
        ]:
            expect(text, needle, failures, "current_plan")

    if FILES["roadmap"].exists():
        text = FILES["roadmap"].read_text(encoding="utf-8")
        for needle in [
            "System Reliability Hardening Track",
            "Candidate Next Lanes",
            "Governance -> Runtime Control",
            "Portfolio Intelligence",
        ]:
            expect(text, needle, failures, "roadmap")

    if FILES["migration_map"].exists():
        text = FILES["migration_map"].read_text(encoding="utf-8")
        for needle in [
            "03_plans/README.md",
            "03_plans/current.md",
            "03_plans/roadmap.md",
        ]:
            expect(text, needle, failures, "migration_map")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

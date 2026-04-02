from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

FILES = {
    "reports_index": REPO_ROOT / "docs" / "11_reports" / "README.md",
    "current_status": REPO_ROOT / "docs" / "11_reports" / "current_status.md",
    "historical_reports": REPO_ROOT / "docs" / "11_reports" / "historical_reports.md",
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

    if FILES["reports_index"].exists():
        text = FILES["reports_index"].read_text(encoding="utf-8")
        for needle in [
            "Read First Now",
            "current_status.md",
            "historical_reports.md",
            "Do not infer the current state only from older phase completion reports.",
        ]:
            expect(text, needle, failures, "reports_index")

    if FILES["current_status"].exists():
        text = FILES["current_status"].read_text(encoding="utf-8")
        for needle in [
            "11 / 11",
            "System Reliability Hardening Track",
            "Execution Reality",
        ]:
            expect(text, needle, failures, "current_status")

    if FILES["historical_reports"].exists():
        text = FILES["historical_reports"].read_text(encoding="utf-8")
        for needle in [
            "Phase Completion Reports",
            "Post_Phase7_hardening_architect_report_2026-04-02.md",
            "Use `current_status.md` to answer:",
        ]:
            expect(text, needle, failures, "historical_reports")

    if FILES["migration_map"].exists():
        text = FILES["migration_map"].read_text(encoding="utf-8")
        for needle in [
            "11_reports/README.md",
            "11_reports/current_status.md",
            "11_reports/historical_reports.md",
        ]:
            expect(text, needle, failures, "migration_map")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

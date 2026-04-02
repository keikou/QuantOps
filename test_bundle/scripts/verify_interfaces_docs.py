from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_DOC = REPO_ROOT / "docs" / "07_interfaces" / "README.md"
CONTRACT_DOC = REPO_ROOT / "docs" / "07_interfaces" / "current_contracts.md"
MAP_DOC = REPO_ROOT / "docs" / "00_index" / "current_docs_migration_map.md"


def expect(text: str, needle: str, failures: list[str], label: str) -> None:
    if needle not in text:
        failures.append(f"{label}_missing:{needle}")


def main() -> None:
    failures: list[str] = []

    for label, path in {
        "index": INDEX_DOC,
        "contracts": CONTRACT_DOC,
        "map": MAP_DOC,
    }.items():
        if not path.exists():
            failures.append(f"missing:{label}")

    if INDEX_DOC.exists():
        text = INDEX_DOC.read_text(encoding="utf-8")
        for needle in [
            "Current Canonical Interface Docs",
            "api-summary-contracts.md",
            "portfolio-display-semantics.md",
            "architecture-read-models.md",
            "event_contracts.md",
        ]:
            expect(text, needle, failures, "index")

    if CONTRACT_DOC.exists():
        text = CONTRACT_DOC.read_text(encoding="utf-8")
        for needle in [
            "stable_value",
            "display_value",
            "truth rows and display rows are not the same thing",
            "truth layer is authoritative",
        ]:
            expect(text, needle, failures, "contracts")

    if MAP_DOC.exists():
        text = MAP_DOC.read_text(encoding="utf-8")
        for needle in [
            "## 07_interfaces",
            "portfolio-display-semantics.md",
            "architecture-read-models.md",
        ]:
            expect(text, needle, failures, "map")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

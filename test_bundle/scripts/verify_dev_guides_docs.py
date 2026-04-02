from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

FILES = {
    "dev_guides_index": REPO_ROOT / "docs" / "08_dev_guides" / "README.md",
    "current_dev_guide": REPO_ROOT / "docs" / "08_dev_guides" / "current_dev_guide.md",
    "verification_guide": REPO_ROOT / "docs" / "08_dev_guides" / "verification_guide.md",
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

    if FILES["dev_guides_index"].exists():
        text = FILES["dev_guides_index"].read_text(encoding="utf-8")
        for needle in [
            "Read First",
            "current_dev_guide.md",
            "verification_guide.md",
            "Execution Reality",
        ]:
            expect(text, needle, failures, "dev_guides_index")

    if FILES["current_dev_guide"].exists():
        text = FILES["current_dev_guide"].read_text(encoding="utf-8")
        for needle in [
            "V12` = correctness-first truth/runtime layer",
            "do not restart `Cross-Phase Acceptance`",
            "Execution Reality",
        ]:
            expect(text, needle, failures, "current_dev_guide")

    if FILES["verification_guide"].exists():
        text = FILES["verification_guide"].read_text(encoding="utf-8")
        for needle in [
            "run the narrowest relevant verifier first",
            "verify_docs_structure_index.py",
            "run_local_startup_smoke.ps1",
        ]:
            expect(text, needle, failures, "verification_guide")

    if FILES["migration_map"].exists():
        text = FILES["migration_map"].read_text(encoding="utf-8")
        for needle in [
            "08_dev_guides/README.md",
            "08_dev_guides/current_dev_guide.md",
            "08_dev_guides/verification_guide.md",
        ]:
            expect(text, needle, failures, "migration_map")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

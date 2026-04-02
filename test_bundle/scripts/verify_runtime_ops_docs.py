from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

FILES = {
    "runtime_ops_index": REPO_ROOT / "docs" / "09_runtime_ops" / "README.md",
    "current_runtime_ops": REPO_ROOT / "docs" / "09_runtime_ops" / "current_runtime_ops.md",
    "incident_and_tracing": REPO_ROOT / "docs" / "09_runtime_ops" / "incident_and_tracing.md",
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

    if FILES["runtime_ops_index"].exists():
        text = FILES["runtime_ops_index"].read_text(encoding="utf-8")
        for needle in [
            "Read First",
            "current_runtime_ops.md",
            "incident_and_tracing.md",
            "correlation-logging-guide.md",
        ]:
            expect(text, needle, failures, "runtime_ops_index")

    if FILES["current_runtime_ops"].exists():
        text = FILES["current_runtime_ops"].read_text(encoding="utf-8")
        for needle in [
            "127.0.0.1",
            "run_all.cmd",
            "not broad re-debugging of already closed system slices",
        ]:
            expect(text, needle, failures, "current_runtime_ops")

    if FILES["incident_and_tracing"].exists():
        text = FILES["incident_and_tracing"].read_text(encoding="utf-8")
        for needle in [
            "trace_id",
            "A conversation claim is not runtime evidence.",
            "SprintH_completion_report.md",
        ]:
            expect(text, needle, failures, "incident_and_tracing")

    if FILES["migration_map"].exists():
        text = FILES["migration_map"].read_text(encoding="utf-8")
        for needle in [
            "09_runtime_ops/README.md",
            "09_runtime_ops/current_runtime_ops.md",
            "09_runtime_ops/incident_and_tracing.md",
        ]:
            expect(text, needle, failures, "migration_map")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

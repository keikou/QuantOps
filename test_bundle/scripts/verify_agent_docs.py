from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

FILES = {
    "agent_index": REPO_ROOT / "docs" / "10_agent" / "README.md",
    "system_context": REPO_ROOT / "docs" / "10_agent" / "system_context.md",
    "rules": REPO_ROOT / "docs" / "10_agent" / "rules.md",
    "capabilities": REPO_ROOT / "docs" / "10_agent" / "capabilities.md",
    "constraints": REPO_ROOT / "docs" / "10_agent" / "constraints.md",
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

    if FILES["agent_index"].exists():
        text = FILES["agent_index"].read_text(encoding="utf-8")
        for needle in [
            "system_context.md",
            "rules.md",
            "capabilities.md",
            "constraints.md",
            "Execution Reality",
        ]:
            expect(text, needle, failures, "agent_index")

    if FILES["system_context"].exists():
        text = FILES["system_context"].read_text(encoding="utf-8")
        for needle in [
            "11 / 11",
            "Execution Reality",
            "older conversation state",
        ]:
            expect(text, needle, failures, "system_context")

    if FILES["rules"].exists():
        text = FILES["rules"].read_text(encoding="utf-8")
        for needle in [
            "do not restart completed hardening packets unless a real regression is found",
            "do not rename the track to `Phase8`",
        ]:
            expect(text, needle, failures, "rules")

    if FILES["capabilities"].exists():
        text = FILES["capabilities"].read_text(encoding="utf-8")
        for needle in [
            "Codex should own",
            "ChatGPT app should own",
            "Use ChatGPT app for decision framing.",
        ]:
            expect(text, needle, failures, "capabilities")

    if FILES["constraints"].exists():
        text = FILES["constraints"].read_text(encoding="utf-8")
        for needle in [
            "Cross-Phase Acceptance` is already completed and verified",
            "Do not ask architect the old question:",
            "completed hardening/resume slice",
        ]:
            expect(text, needle, failures, "constraints")

    if FILES["migration_map"].exists():
        text = FILES["migration_map"].read_text(encoding="utf-8")
        for needle in [
            "10_agent/README.md",
            "10_agent/system_context.md",
            "10_agent/rules.md",
            "10_agent/capabilities.md",
            "10_agent/constraints.md",
        ]:
            expect(text, needle, failures, "migration_map")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

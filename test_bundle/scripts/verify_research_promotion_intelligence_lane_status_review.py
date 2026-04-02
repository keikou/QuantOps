from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "Research_promotion_intelligence_lane_status_review_2026-04-02.md"


def main() -> None:
    failures: list[str] = []

    if not DOC.exists():
        failures.append("missing_lane_status_review_doc")
    else:
        text = DOC.read_text(encoding="utf-8")
        for needle in [
            "RPI-01: Promotion Agenda Surface",
            "RPI-02: Promotion Candidate Docket",
            "RPI-03: Review Queue Surface",
            "RPI-04: Review Board Slate",
            "RPI-05: Deterministic Review Outcome Resolution",
            "RPI-06: Persisted Governed State Transition",
            "first state-applied checkpoint",
        ]:
            if needle not in text:
                failures.append(f"doc_missing:{needle}")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

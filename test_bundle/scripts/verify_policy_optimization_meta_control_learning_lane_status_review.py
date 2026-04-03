from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "Policy_optimization_meta_control_learning_lane_status_review_2026-04-03.md"


def main() -> None:
    failures: list[str] = []

    if not DOC.exists():
        failures.append("missing_lane_status_review_doc")
    else:
        text = DOC.read_text(encoding="utf-8")
        for needle in [
            "PO-01",
            "PO-02",
            "PO-03",
            "PO-04",
            "PO-05",
            "/system/policy-effectiveness/latest",
            "/system/meta-policy-effectiveness/latest",
            "meta-policy outcome-visible checkpoint",
        ]:
            if needle not in text:
                failures.append(f"doc_missing:{needle}")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

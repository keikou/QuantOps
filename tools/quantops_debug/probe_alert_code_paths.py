from pathlib import Path
import re

ROOT = Path(".").resolve()

PATTERNS = {
    "risk_limit_drawdown": [
        r"drawdown",
        r"risk_limit",
        r"default",
    ],
    "alert_evaluator": [
        r"alert_evaluator",
        r"evaluate_alert",
        r"alerts",
        r"breach",
        r"alert_state",
    ],
    "scheduler_jobs": [
        r"add_job",
        r"scheduler",
        r"alert",
    ],
}

TARGET_DIRS = [
    ROOT / "apps" / "quantops-api",
    ROOT / "tools",
]

EXTS = {".py", ".yaml", ".yml", ".toml", ".json"}


def scan_file(path: Path, keywords: list[str]) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        try:
            text = path.read_text(encoding="utf-8-sig")
        except Exception:
            return []
    hits = []
    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        low = line.lower()
        if all(k.lower() in low for k in keywords[:1]) or any(k.lower() in low for k in keywords):
            hits.append(f"{path}:{i}: {line.strip()}")
    return hits[:20]


def main():
    for label, keywords in PATTERNS.items():
        print(f"\n=== {label} ===")
        total = 0
        for base in TARGET_DIRS:
            if not base.exists():
                continue
            for p in base.rglob("*"):
                if p.suffix.lower() not in EXTS:
                    continue
                hits = scan_file(p, keywords)
                for h in hits[:10]:
                    print(h)
                    total += 1
                    if total >= 30:
                        break
                if total >= 30:
                    break
            if total >= 30:
                break
        if total == 0:
            print("No hits")


if __name__ == "__main__":
    main()
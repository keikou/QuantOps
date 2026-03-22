import sys
import time
from typing import Any, Dict, List, Optional

import requests

API = "http://localhost:8010/api/v1"


def get_json(path: str) -> Any:
    url = f"{API}{path}"
    r = requests.get(url, timeout=5)
    r.raise_for_status()
    return r.json()


def safe_get_json(path: str) -> Optional[Any]:
    try:
        return get_json(path)
    except Exception as e:
        print(f"[WARN] GET {path} failed: {e}")
        return None


def find_job_items(scheduler_payload: Any) -> List[Dict[str, Any]]:
    if scheduler_payload is None:
        return []
    if isinstance(scheduler_payload, list):
        return scheduler_payload
    if isinstance(scheduler_payload, dict):
        if isinstance(scheduler_payload.get("items"), list):
            return scheduler_payload["items"]
        if isinstance(scheduler_payload.get("jobs"), list):
            return scheduler_payload["jobs"]
    return []


def find_alert_items(alerts_payload: Any) -> List[Dict[str, Any]]:
    if alerts_payload is None:
        return []
    if isinstance(alerts_payload, list):
        return alerts_payload
    if isinstance(alerts_payload, dict):
        if isinstance(alerts_payload.get("items"), list):
            return alerts_payload["items"]
        if isinstance(alerts_payload.get("alerts"), list):
            return alerts_payload["alerts"]
    return []


def main() -> int:
    print("QuantOps Alert Root Cause Probe")
    print("================================\n")

    risk1 = safe_get_json("/risk/snapshot")
    alerts = safe_get_json("/alerts")
    scheduler = safe_get_json("/scheduler/jobs")

    time.sleep(3)
    risk2 = safe_get_json("/risk/snapshot")

    if not risk1:
        print("[FAIL] /risk/snapshot を取得できません")
        return 1

    print("[1] Risk snapshot")
    print(risk1)

    drawdown = risk1.get("drawdown")
    risk_limit = risk1.get("risk_limit") or {}
    dd_limit = risk_limit.get("drawdown")
    alert_state = risk1.get("alert_state")
    alert = risk1.get("alert")
    kill_switch = risk1.get("kill_switch")
    trading_state = risk1.get("trading_state")
    as_of_1 = risk1.get("as_of")
    as_of_2 = risk2.get("as_of") if isinstance(risk2, dict) else None

    print("\n[2] Risk breach 判定チェック")
    if dd_limit is None:
        print("  [WARN] risk_limit.drawdown が存在しません")
    else:
        print(f"  drawdown={drawdown}")
        print(f"  limit.drawdown={dd_limit}")
        if isinstance(drawdown, (int, float)) and isinstance(dd_limit, (int, float)):
            if drawdown > dd_limit:
                print("  [INFO] drawdown breach 条件を満たしています")
            else:
                print("  [INFO] drawdown breach 条件は満たしていません")

    print("\n[3] Alert state / trading state")
    print(f"  alert_state={alert_state}")
    print(f"  alert={alert}")
    print(f"  kill_switch={kill_switch}")
    print(f"  trading_state={trading_state}")

    if kill_switch == "triggered" and trading_state == "running":
        print("  [FAIL] kill_switch=triggered なのに trading_state=running です")
    else:
        print("  [PASS] kill_switch と trading_state の整合に大きな矛盾は見えません")

    print("\n[4] Alerts")
    alert_items = find_alert_items(alerts)
    print(f"  alerts_count={len(alert_items)}")
    if len(alert_items) == 0 and (alert_state == "breach" or alert == "breach"):
        print("  [FAIL] risk は breach だが alerts は空です")
    else:
        print("  [PASS] alerts 状態に重大な矛盾は見えません")

    print("\n[5] Scheduler")
    jobs = find_job_items(scheduler)
    print(f"  scheduler_jobs_count={len(jobs)}")

    alert_job_names = []
    for j in jobs:
        name = str(j.get("job_id") or j.get("id") or j.get("name") or "").lower()
        if "alert" in name:
            alert_job_names.append(name)

    if alert_job_names:
        print(f"  [INFO] alert系 job 検出: {alert_job_names}")
    else:
        print("  [FAIL] scheduler に alert 系 job が見つかりません")

    print("\n[6] Stale snapshot")
    print(f"  as_of first ={as_of_1}")
    print(f"  as_of second={as_of_2}")
    if as_of_1 and as_of_2 and as_of_1 == as_of_2:
        print("  [WARN] risk snapshot の as_of が変わっていません。stale の可能性があります")
    else:
        print("  [PASS] risk snapshot の as_of は変化しています")

    print("\n[7] Root cause summary")
    findings = []

    if isinstance(drawdown, (int, float)) and isinstance(dd_limit, (int, float)) and dd_limit == 0.0:
        findings.append("risk_limit.drawdown=0.0 が常時 breach を起こしている可能性が高い")

    if len(alert_items) == 0 and (alert_state == "breach" or alert == "breach"):
        findings.append("alert evaluator 未実行、または risk->alerts の schema mismatch")

    if not alert_job_names:
        findings.append("scheduler に alert evaluator job が登録されていない可能性が高い")

    if kill_switch == "triggered" and trading_state == "running":
        findings.append("risk state と trading state の連携不整合")

    if as_of_1 and as_of_2 and as_of_1 == as_of_2:
        findings.append("risk snapshot stale の可能性")

    if findings:
        for idx, f in enumerate(findings, start=1):
            print(f"  {idx}. {f}")
        return 1

    print("  重大な根本原因はこのプローブでは検出されませんでした")
    return 0


if __name__ == "__main__":
    sys.exit(main())
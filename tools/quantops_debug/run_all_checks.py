from __future__ import annotations

try:
    from .check_alert_pipeline import check_alerts
    from .check_dashboard_consistency import check_dashboard
    from .check_execution_consistency import check_execution
    from .check_monitoring import check_monitoring
    from .check_portfolio_consistency import check_portfolio
except ImportError:  # direct script execution
    from check_alert_pipeline import check_alerts
    from check_dashboard_consistency import check_dashboard
    from check_execution_consistency import check_execution
    from check_monitoring import check_monitoring
    from check_portfolio_consistency import check_portfolio


def run() -> int:
    print("\nQuantOps System Diagnostics")
    print("===========================\n")
    checks = [
        ("Portfolio state", check_portfolio),
        ("Execution analytics", check_execution),
        ("Dashboard consistency", check_dashboard),
        ("Monitoring metrics", check_monitoring),
        ("Alert pipeline", check_alerts),
    ]
    failures = 0
    for name, fn in checks:
        try:
            fn()
            print(f"{name:<30} PASS")
        except Exception as exc:  # noqa: BLE001
            print(f"{name:<30} FAIL")
            print(f"  {exc}")
            failures += 1
    if failures:
        print("\nSystem has inconsistencies\n")
        return 1
    print("\nAll checks passed\n")
    return 0


if __name__ == '__main__':
    raise SystemExit(run())

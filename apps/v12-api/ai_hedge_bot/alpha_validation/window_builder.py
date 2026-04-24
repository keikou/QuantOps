from __future__ import annotations

from datetime import UTC, datetime, timedelta


class WindowBuilder:
    def build(self, *, alpha_id: str, min_windows: int = 4) -> list[dict]:
        anchor = datetime(2026, 4, 25, tzinfo=UTC)
        train_days = 90
        test_days = 30
        step_days = 30
        items = []
        for idx in range(max(min_windows, 4)):
            test_end = anchor - timedelta(days=(step_days * idx))
            test_start = test_end - timedelta(days=test_days)
            train_end = test_start - timedelta(days=1)
            train_start = train_end - timedelta(days=train_days)
            items.append(
                {
                    "alpha_id": alpha_id,
                    "window_id": f"{alpha_id}.wf.{idx + 1}",
                    "train_start": train_start.isoformat(),
                    "train_end": train_end.isoformat(),
                    "test_start": test_start.isoformat(),
                    "test_end": test_end.isoformat(),
                    "symbol": "MULTI",
                    "regime": "balanced" if idx % 2 == 0 else "transition",
                }
            )
        return list(reversed(items))


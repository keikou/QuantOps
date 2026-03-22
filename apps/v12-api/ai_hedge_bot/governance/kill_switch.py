from __future__ import annotations

from typing import Any


class KillSwitch:
    def trigger_kill_switch(self, risk_snapshot: dict[str, Any]) -> dict[str, Any]:
        risk_flag = bool(risk_snapshot.get('risk_flag', False))
        reasons = list(risk_snapshot.get('risk_reasons', []))
        return {
            'kill_switch_active': risk_flag,
            'reasons': reasons,
            'action': 'halt_new_execution' if risk_flag else 'continue',
        }

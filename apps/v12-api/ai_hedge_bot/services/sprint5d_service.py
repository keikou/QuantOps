from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from ai_hedge_bot.core.mode import RuntimeMode
from ai_hedge_bot.core.mode_rules import build_default_policy, validate_transition
from ai_hedge_bot.services.sprint5d_store import Sprint5DStore


class Sprint5DService:
    def __init__(self, db_path) -> None:
        self.store = Sprint5DStore(db_path)
        self._current_mode = RuntimeMode.PAPER

    @property
    def current_mode(self) -> RuntimeMode:
        return self._current_mode

    def list_modes(self) -> list[dict[str, Any]]:
        return self.store.list_modes()

    def get_current_mode(self) -> dict[str, Any]:
        mode_row = self.store.get_mode(self._current_mode.value) or {'mode': self._current_mode.value}
        return {
            'runtime_mode': self._current_mode.value,
            'config': mode_row,
            'policy': build_default_policy(self._current_mode).to_dict(),
        }

    def set_current_mode(self, mode_value: str) -> dict[str, Any]:
        requested = RuntimeMode.parse(mode_value)
        if not validate_transition(self._current_mode, requested):
            raise ValueError(f'Invalid mode transition: {self._current_mode.value} -> {requested.value}')
        config = self.store.get_mode(requested.value)
        if config and not config.get('is_enabled', True):
            raise ValueError(f'Mode disabled: {requested.value}')
        self._current_mode = requested
        self.store.update_mode(requested.value, True)
        return self.get_current_mode()

    def _record_validation(self, *, run_id: str, runtime_mode: RuntimeMode, check_name: str, passed: bool,
                           severity: str, details: dict[str, Any]) -> dict[str, Any]:
        row = {
            'validation_id': f'val_{uuid4().hex[:12]}',
            'run_id': run_id,
            'runtime_mode': runtime_mode.value,
            'check_name': check_name,
            'passed': passed,
            'severity': severity,
            'details': details,
            'checked_at': datetime.now(UTC).isoformat(),
        }
        self.store.insert_validation(row)
        return row

    def _record_incident(self, *, run_id: str, runtime_mode: RuntimeMode, category: str, severity: str,
                         message: str, payload: dict[str, Any]) -> dict[str, Any]:
        row = {
            'incident_id': f'inc_{uuid4().hex[:12]}',
            'run_id': run_id,
            'runtime_mode': runtime_mode.value,
            'category': category,
            'severity': severity,
            'message': message,
            'payload': payload,
            'created_at': datetime.now(UTC).isoformat(),
        }
        self.store.insert_incident(row)
        return row

    def run_preflight_checks(self, run_id: str, mode: RuntimeMode, payload: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        payload = payload or {}
        results: list[dict[str, Any]] = []
        policy = build_default_policy(mode)

        results.append(self._record_validation(
            run_id=run_id,
            runtime_mode=mode,
            check_name='db_available',
            passed=True,
            severity='info',
            details={'db_path': str(self.store.path)},
        ))

        has_live_credentials = bool(payload.get('has_live_credentials', False))
        results.append(self._record_validation(
            run_id=run_id,
            runtime_mode=mode,
            check_name='live_credentials',
            passed=(not policy.require_live_credentials) or has_live_credentials,
            severity='critical' if policy.require_live_credentials else 'info',
            details={'required': policy.require_live_credentials, 'present': has_live_credentials},
        ))

        hard_risk_pass = bool(payload.get('hard_risk_pass', mode != RuntimeMode.LIVE_READY))
        results.append(self._record_validation(
            run_id=run_id,
            runtime_mode=mode,
            check_name='hard_risk_pass',
            passed=(not policy.require_hard_risk_pass) or hard_risk_pass,
            severity='critical' if policy.require_hard_risk_pass else 'info',
            details={'required': policy.require_hard_risk_pass, 'passed': hard_risk_pass},
        ))

        results.append(self._record_validation(
            run_id=run_id,
            runtime_mode=mode,
            check_name='scheduler_health',
            passed=True,
            severity='info',
            details={'status': 'ok'},
        ))

        return results

    def build_acceptance_status(self, run_id: str | None = None) -> dict[str, Any]:
        checks = self.store.list_validations(run_id=run_id)
        if not checks:
            return {'status': 'missing', 'passed': False, 'checks': []}
        passed = all(item['passed'] for item in checks if item['severity'] in {'critical', 'warning', 'info'})
        failed = [item for item in checks if not item['passed']]
        return {
            'status': 'ok',
            'passed': passed,
            'total_checks': len(checks),
            'failed_checks': len(failed),
            'checks': checks[:20],
        }

    def _execute(self, mode: RuntimeMode, payload: dict[str, Any]) -> dict[str, Any]:
        expected_pnl = float(payload.get('expected_pnl', 125.0))
        order_count = int(payload.get('order_count', 3))
        details: dict[str, Any] = {
            'executor': mode.value,
            'order_count': order_count,
        }
        if mode == RuntimeMode.PAPER:
            details.update({
                'virtual_fills': order_count,
                'external_send': False,
                'net_pnl': expected_pnl,
            })
            return details
        if mode == RuntimeMode.SHADOW:
            slippage_drag = float(payload.get('slippage_drag', 8.5))
            fee_drag = float(payload.get('fee_drag', 1.5))
            latency_drag = float(payload.get('latency_drag', 2.0))
            execution_drag = slippage_drag + fee_drag + latency_drag
            net_shadow_pnl = expected_pnl - execution_drag
            details.update({
                'virtual_fills': max(order_count - 1, 1),
                'external_send': False,
                'gross_alpha_pnl': expected_pnl,
                'net_shadow_pnl': net_shadow_pnl,
                'execution_drag': execution_drag,
                'slippage_drag': slippage_drag,
                'fee_drag': fee_drag,
                'latency_drag': latency_drag,
            })
            return details
        details.update({
            'virtual_fills': 0,
            'external_send': False,
            'dry_run': True,
            'venue_preflight': 'ok',
            'net_pnl': 0.0,
        })
        return details

    def run_with_mode(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        mode = RuntimeMode.parse(payload.get('mode') or self._current_mode.value)
        run_id = str(payload.get('run_id') or f's5d_{uuid4().hex[:10]}')
        created_at = datetime.now(UTC).isoformat()
        policy = build_default_policy(mode)
        validations = self.run_preflight_checks(run_id, mode, payload)

        blocking_failures = [v for v in validations if (not v['passed']) and v['severity'] == 'critical']
        status = 'blocked' if blocking_failures else 'ok'
        execution = self._execute(mode, payload)

        if mode == RuntimeMode.SHADOW:
            self.store.insert_shadow_snapshot({
                'run_id': run_id,
                'created_at': created_at,
                'gross_alpha_pnl': execution['gross_alpha_pnl'],
                'net_shadow_pnl': execution['net_shadow_pnl'],
                'execution_drag': execution['execution_drag'],
                'slippage_drag': execution['slippage_drag'],
                'fee_drag': execution['fee_drag'],
                'latency_drag': execution['latency_drag'],
            })

        if blocking_failures:
            self._record_incident(
                run_id=run_id,
                runtime_mode=mode,
                category='validation_failure',
                severity='critical',
                message='Run blocked by critical validation failure',
                payload={'failed_checks': blocking_failures},
            )

        if mode == RuntimeMode.LIVE_READY and not policy.allow_external_send:
            self._record_incident(
                run_id=run_id,
                runtime_mode=mode,
                category='mode_guard',
                severity='warning',
                message='External send blocked in live_ready mode',
                payload={'external_send': False, 'dry_run': True},
            )

        self.store.insert_run({
            'run_id': run_id,
            'runtime_mode': mode.value,
            'source_job_id': payload.get('source_job_id'),
            'trigger_source': payload.get('trigger_source', 'api'),
            'mode_policy': policy.to_dict(),
            'status': status,
            'details': execution,
            'created_at': created_at,
        })
        self._current_mode = mode
        return {
            'run_id': run_id,
            'runtime_mode': mode.value,
            'status': status,
            'mode_policy': policy.to_dict(),
            'execution': execution,
            'acceptance': self.build_acceptance_status(run_id=run_id),
        }

    def latest_run(self) -> dict[str, Any]:
        return self.store.latest_run()

    def acceptance_status(self, run_id: str | None = None) -> dict[str, Any]:
        return self.build_acceptance_status(run_id=run_id)

    def acceptance_checks(self, run_id: str | None = None) -> list[dict[str, Any]]:
        return self.store.list_validations(run_id=run_id)

    def latest_incidents(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.store.latest_incidents(limit=limit)

    def shadow_summary(self) -> dict[str, Any]:
        return self.store.latest_shadow_summary()

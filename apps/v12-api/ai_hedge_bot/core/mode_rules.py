from __future__ import annotations

from ai_hedge_bot.core.mode import ModePolicy, RuntimeMode


def build_default_policy(mode: RuntimeMode) -> ModePolicy:
    if mode == RuntimeMode.PAPER:
        return ModePolicy(
            mode=mode.value,
            allow_market_data_live=False,
            allow_virtual_fills=True,
            allow_external_send=False,
            allow_state_commit=True,
            allow_shadow_latency_model=False,
            require_live_credentials=False,
            require_hard_risk_pass=False,
        )
    if mode == RuntimeMode.SHADOW:
        return ModePolicy(
            mode=mode.value,
            allow_market_data_live=True,
            allow_virtual_fills=True,
            allow_external_send=False,
            allow_state_commit=True,
            allow_shadow_latency_model=True,
            require_live_credentials=False,
            require_hard_risk_pass=False,
        )
    if mode == RuntimeMode.LIVE_READY:
        return ModePolicy(
            mode=mode.value,
            allow_market_data_live=True,
            allow_virtual_fills=False,
            allow_external_send=False,
            allow_state_commit=True,
            allow_shadow_latency_model=False,
            require_live_credentials=True,
            require_hard_risk_pass=True,
        )
    raise ValueError(f'Unsupported runtime mode: {mode}')


def validate_transition(from_mode: RuntimeMode, to_mode: RuntimeMode) -> bool:
    allowed = {
        RuntimeMode.PAPER: {RuntimeMode.PAPER, RuntimeMode.SHADOW},
        RuntimeMode.SHADOW: {RuntimeMode.SHADOW, RuntimeMode.LIVE_READY, RuntimeMode.PAPER},
        RuntimeMode.LIVE_READY: {RuntimeMode.LIVE_READY, RuntimeMode.PAPER, RuntimeMode.SHADOW},
    }
    return to_mode in allowed[from_mode]

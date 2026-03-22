from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter

from ai_hedge_bot.core.ids import new_run_id, new_cycle_id
from ai_hedge_bot.core.clock import utc_now_iso


@dataclass
class StepContext:
    step_id: str
    step_name: str
    started_at: str
    started_perf: float = field(default_factory=perf_counter)


@dataclass
class RunContext:
    job_name: str
    mode: str
    triggered_by: str = 'api'
    run_id: str = field(default_factory=new_run_id)
    started_at: str = field(default_factory=utc_now_iso)
    started_perf: float = field(default_factory=perf_counter)

    def new_step(self, step_name: str) -> StepContext:
        return StepContext(step_id=new_cycle_id(), step_name=step_name, started_at=utc_now_iso())

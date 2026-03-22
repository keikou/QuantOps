from __future__ import annotations

EXECUTION_JOB_KEYWORDS = ("execution", "runtime", "orchestrator", "paper", "rebalance")


def is_execution_job(job: dict | None = None, *, job_id: str | None = None, job_name: str | None = None, job_group: str | None = None) -> bool:
    values = []
    if job:
        values.extend([str(job.get("job_id", "") or ""), str(job.get("job_name", "") or ""), str(job.get("job_group", "") or "")])
    values.extend([str(job_id or ""), str(job_name or ""), str(job_group or "")])
    haystack = " ".join(values).lower()
    return any(token in haystack for token in EXECUTION_JOB_KEYWORDS)


def derive_effective_job_status(enabled: bool, trading_state: str, execution_job: bool) -> str:
    state = str(trading_state or "running").lower()
    if execution_job and state in {"halted", "paused"}:
        return state
    return "running" if enabled else "paused"


def should_block_execution(trading_state: str, execution_job: bool = True) -> bool:
    state = str(trading_state or "running").lower()
    return execution_job and state in {"halted", "paused"}

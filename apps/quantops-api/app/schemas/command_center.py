from __future__ import annotations

from pydantic import BaseModel, Field


class CommandCenterOverviewResponse(BaseModel):
    status: str = "ok"
    portfolio_value: float
    pnl: float
    gross_exposure: float
    net_exposure: float
    active_strategies: int
    open_alerts: int
    scheduler_jobs: int
    fill_rate: float
    avg_slippage_bps: float
    system_status: str
    as_of: str


class CommandCenterStrategyItem(BaseModel):
    strategy_id: str
    strategy_name: str
    capital_weight: float = 0.0
    realized_return: float = 0.0
    risk_budget_usage: float = 0.0
    risk_budget: float | None = None
    status: str = "enabled"
    remote_status: str = "unknown"
    updated_at: str | None = None


class CommandCenterStrategiesResponse(BaseModel):
    status: str = "ok"
    enabled_count: int = 0
    items: list[CommandCenterStrategyItem] = Field(default_factory=list)
    as_of: str


class CommandCenterExecutionLatestResponse(BaseModel):
    status: str = "ok"
    order_count: int = 0
    fill_count: int = 0
    fill_rate: float = 0.0
    avg_slippage_bps: float = 0.0
    latency_ms_p50: float = 0.0
    latency_ms_p95: float = 0.0
    venue_score: float = 0.0
    as_of: str


class CommandCenterPortfolioSummaryResponse(BaseModel):
    status: str = "ok"
    portfolio_value: float
    cash: float
    pnl: float
    drawdown: float
    gross_exposure: float
    net_exposure: float
    long_exposure: float
    short_exposure: float
    leverage: float
    position_count: int
    as_of: str


class CommandCenterRiskSummaryResponse(BaseModel):
    status: str = "ok"
    gross_exposure: float
    net_exposure: float
    leverage: float
    drawdown: float
    alert_state: str
    risk_limit: dict = Field(default_factory=dict)
    trading_state: str = "running"
    as_of: str


class CommandCenterSystemSummaryResponse(BaseModel):
    status: str = "ok"
    system_status: str
    execution_status: str
    services: dict = Field(default_factory=dict)
    open_alerts: int = 0
    scheduler_jobs: int = 0
    as_of: str



class CommandCenterStrategyActionRequest(BaseModel):
    strategy_id: str


class CommandCenterStrategyRiskUpdateRequest(BaseModel):
    strategy_id: str
    risk_budget: float
    note: str | None = None


class CommandCenterRiskActionRequest(BaseModel):
    note: str | None = None


class CommandCenterRuntimeRunReviewRequest(BaseModel):
    review_status: str
    acknowledged: bool | None = None
    operator_note: str | None = None


class CommandCenterRuntimeIssueAcknowledgeRequest(BaseModel):
    note: str | None = None


class CommandCenterActionResponse(BaseModel):
    ok: bool = True
    message: str
    action: str
    target: str
    details: dict = Field(default_factory=dict)
    as_of: str



class CommandCenterHardeningStatusResponse(BaseModel):
    status: str = 'ok'
    rbac_enabled: bool = True
    audit_enabled: bool = True
    notification_channels: dict = Field(default_factory=dict)
    operator_actions_logged: int = 0
    kill_switch_events: int = 0
    recent_audit_events: int = 0
    as_of: str


class CommandCenterAuditSummaryResponse(BaseModel):
    status: str = 'ok'
    audit_logs: list[dict] = Field(default_factory=list)
    operator_actions: list[dict] = Field(default_factory=list)
    config_changes: list[dict] = Field(default_factory=list)
    mode_switches: list[dict] = Field(default_factory=list)
    kill_switch_events: list[dict] = Field(default_factory=list)
    as_of: str

import type { CommandCenterRuntimeDebug, CommandCenterRuntimeLatest, DataSourceStatus, DataStatus, MonitoringSystem, RiskSnapshot, UserRole } from '@/types/api';

export function getPayload<T>(input: any, fallback: T): T {
  if (input == null) return fallback;
  if (typeof input === 'object') {
    if ('data' in input && input.data != null) {
      const inner = (input as any).data;
      if (inner && typeof inner === 'object' && 'data' in inner && (inner as any).data != null) {
        return (inner as any).data as T;
      }
      return inner as T;
    }
    if ('item' in input && (input as any).item != null) return (input as any).item as T;
  }
  return input as T;
}

export function getArray<T>(input: any): T[] {
  if (Array.isArray(input)) return input as T[];
  if (input == null) return [];

  const payload = getPayload<any>(input, input);
  if (Array.isArray(payload)) return payload as T[];
  if (payload == null) return [];

  const candidates = [
    payload.items,
    payload.rows,
    payload.results,
    payload.strategies,
    payload.approvals,
    payload.logs,
    payload.alerts,
    payload.jobs,
    payload.positions,
  ];
  for (const c of candidates) {
    if (Array.isArray(c)) return c as T[];
  }
  return [];
}

const USER_ROLES: UserRole[] = ['viewer', 'operator', 'risk_manager', 'admin'];

function isUserRole(value: unknown): value is UserRole {
  return typeof value === 'string' && USER_ROLES.includes(value as UserRole);
}

export function getRole(input: any, fallback: UserRole = 'viewer'): UserRole {
  const payload = getPayload<any>(input, input);
  if (payload && typeof payload === 'object' && isUserRole(payload.role)) return payload.role;
  return fallback;
}

function toNumber(value: any, fallback = 0): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function toString(value: any, fallback = ''): string {
  return typeof value === 'string' ? value : fallback;
}

function toBool(value: any, fallback = false): boolean {
  if (typeof value === 'boolean') return value;
  return fallback;
}

function normalizeStatus(value: any, fallback = 'unknown'): string {
  return typeof value === 'string' && value.length > 0 ? value : fallback;
}

export function normalizeOverview(input: any) {
  const x = getPayload<any>(input, {});
  const alerts = Array.isArray(x.alerts) ? x.alerts : [];
  const jobs = Array.isArray(x.jobs) ? x.jobs : [];
  return {
    totalEquity: toNumber(x.totalEquity ?? x.total_equity ?? x.portfolioValue ?? x.portfolio_value),
    balance: toNumber(x.balance ?? x.cashBalance ?? x.cash_balance ?? x.cash),
    usedMargin: toNumber(x.usedMargin ?? x.used_margin),
    freeMargin: toNumber(x.freeMargin ?? x.free_margin ?? x.freeCash ?? x.free_cash ?? x.available_margin),
    unrealized: toNumber(x.unrealized ?? x.unrealizedPnl ?? x.unrealized_pnl),
    asOf: toString(x.asOf ?? x.as_of),
    dailyPnl: toNumber(x.dailyPnl ?? x.daily_pnl ?? x.pnl ?? x.daily_return),
    grossExposure: toNumber(x.grossExposure ?? x.gross_exposure),
    netExposure: toNumber(x.netExposure ?? x.net_exposure),
    activeStrategies: toNumber(x.activeStrategies ?? x.active_strategies),
    openAlerts: toNumber(x.openAlerts ?? x.open_alerts ?? alerts.length),
    runningJobs: toNumber(x.runningJobs ?? x.running_jobs ?? jobs.length),
    pnlSeries: Array.isArray(x.pnlSeries) ? x.pnlSeries : Array.isArray(x.pnl_series) ? x.pnl_series : [],
    leverage: toNumber(x.leverage),
  };
}

export function normalizePortfolioOverview(input: any) {
  const x = getPayload<any>(input, {});
  return {
    totalEquity: toNumber(x.totalEquity ?? x.total_equity ?? x.portfolioValue ?? x.portfolio_value),
    balance: toNumber(x.balance ?? x.cashBalance ?? x.cash_balance ?? x.cash),
    usedMargin: toNumber(x.usedMargin ?? x.used_margin),
    freeMargin: toNumber(x.freeMargin ?? x.free_margin ?? x.freeCash ?? x.free_cash ?? x.available_margin),
    unrealized: toNumber(x.unrealized ?? x.unrealizedPnl ?? x.unrealized_pnl),
    grossExposure: toNumber(x.grossExposure ?? x.gross_exposure),
    netExposure: toNumber(x.netExposure ?? x.net_exposure),
    realizedPnl: toNumber(x.realizedPnl ?? x.realized_pnl ?? x.realized),
    unrealizedPnl: toNumber(x.unrealizedPnl ?? x.unrealized_pnl ?? x.unrealized),
    expectedVolatility: toNumber(x.expectedVolatility ?? x.expected_volatility ?? x.volatility),
    expectedSharpe: toNumber(x.expectedSharpe ?? x.expected_sharpe ?? x.sharpe),
    lastUpdated: toString(x.lastUpdated ?? x.last_updated ?? x.asOf ?? x.as_of),
  };
}

export function normalizePositions(input: any) {
  return getArray<any>(input).map((p, idx) => ({
    symbol: toString(p.symbol ?? p.ticker ?? p.asset, `row-${idx}`),
    side: (p.side === 'short' ? 'short' : 'long') as 'long' | 'short',
    quantity: toNumber(p.quantity ?? p.qty ?? p.size),
    avgPrice: toNumber(p.avgPrice ?? p.avg_price ?? p.entryPrice ?? p.entry_price),
    markPrice: toNumber(p.markPrice ?? p.mark_price ?? p.price ?? p.last_price),
    pnl: toNumber(p.pnl ?? p.unrealizedPnl ?? p.unrealized_pnl),
    strategyId: toString(p.strategyId ?? p.strategy_id, ''),
    alphaFamily: toString(p.alphaFamily ?? p.alpha_family, ''),
  }));
}

export function normalizeRisk(input: any) {
  const x = getPayload<any>(input, {});
  const tradingStateRaw = toString(x.tradingState ?? x.trading_state, 'running');
  const tradingState = tradingStateRaw === 'paused' ? 'paused' : 'running';
  const dataStatusRaw = normalizeStatus(x.dataStatus ?? x.data_status, 'unknown');
  const dataStatus: DataStatus | undefined = (
    ['ok', 'loading', 'stale', 'timed_out', 'no_data', 'fallback'].includes(dataStatusRaw)
      ? (dataStatusRaw as DataStatus)
      : undefined
  );
  const dataSourceRaw = normalizeStatus(x.dataSource ?? x.data_source, 'unknown');
  const dataSource: DataSourceStatus | undefined = (
    ['live', 'cache', 'empty', 'fallback', 'unknown'].includes(dataSourceRaw)
      ? (dataSourceRaw as DataSourceStatus)
      : undefined
  );
  return {
    grossExposure: toNumber(x.grossExposure ?? x.gross_exposure),
    netExposure: toNumber(x.netExposure ?? x.net_exposure),
    var1d: toNumber(x.var1d ?? x.var_1d ?? x.var_95 ?? x.var),
    drawdown: toNumber(x.drawdown ?? x.maxDrawdown ?? x.max_drawdown),
    concentration: toNumber(x.concentration ?? x.top_weight ?? x.concentration_top_weight),
    killSwitch: normalizeStatus(x.killSwitch ?? x.kill_switch ?? x.alert_state ?? x.alert, 'normal') as 'normal' | 'armed' | 'triggered',
    alert: normalizeStatus(x.alert ?? x.alert_state, 'unknown'),
    tradingState,
    dataStatus,
    dataSource,
    statusReason: toString(x.statusReason ?? x.status_reason, ''),
    isStale: toBool(x.isStale ?? x.is_stale, false),
    asOf: toString(x.asOf ?? x.as_of),
  } satisfies RiskSnapshot;
}

export function normalizeMonitoring(input: any) {
  const x = getPayload<any>(input, {});
  const dataStatusRaw = normalizeStatus(x.dataStatus ?? x.data_status, 'unknown');
  const dataStatus: DataStatus | undefined = (
    ['ok', 'loading', 'stale', 'timed_out', 'no_data', 'fallback'].includes(dataStatusRaw)
      ? (dataStatusRaw as DataStatus)
      : undefined
  );
  const dataSourceRaw = normalizeStatus(x.dataSource ?? x.data_source, 'unknown');
  const dataSource: DataSourceStatus | undefined = (
    ['live', 'cache', 'empty', 'fallback', 'unknown'].includes(dataSourceRaw)
      ? (dataSourceRaw as DataSourceStatus)
      : undefined
  );
  return {
    cpu: toNumber(x.cpu ?? x.cpu_pct ?? x.cpuPercent),
    memory: toNumber(x.memory ?? x.memory_pct ?? x.memoryPercent),
    disk: toString(x.disk ?? x.disk_status, 'unknown'),
    dbWritable: toBool(x.dbWritable ?? x.db_writable, false),
    exchangeLatencyMs: toNumber(x.exchangeLatencyMs ?? x.exchange_latency_ms ?? x.latencyMs ?? x.latency_ms),
    dataFreshnessSec: toNumber(x.dataFreshnessSec ?? x.data_freshness_sec ?? x.freshnessSec),
    exchange: toString(x.exchange ?? x.exchange_status, ''),
    latencyMs: toNumber(x.latencyMs ?? x.latency_ms),
    queue: toNumber(x.queue ?? x.queue_size),
    workerStatus: toString(x.workerStatus ?? x.worker_status, ''),
    executionState: toString(x.executionState ?? x.execution_state ?? x.executionStateLatest, ''),
    executionReason: toString(x.executionReason ?? x.execution_reason ?? x.reason, ''),
    riskTradingState: toString(x.riskTradingState ?? x.risk_trading_state, ''),
    killSwitch: toString(x.killSwitch ?? x.kill_switch, ''),
    alertState: toString(x.alertState ?? x.alert_state ?? x.alert, ''),
    dataStatus,
    dataSource,
    statusReason: toString(x.statusReason ?? x.status_reason, ''),
    isStale: toBool(x.isStale ?? x.is_stale, false),
    asOf: toString(x.asOf ?? x.as_of),
  } satisfies MonitoringSystem;
}

export function normalizeAlerts(input: any) {
  return getArray<any>(input).map((a, idx) => ({
    id: toString(a.id ?? a.alert_id, `alert-${idx}`),
    severity: (toString(a.severity, 'info') as 'info' | 'warning' | 'critical'),
    status: (toString(a.status, 'open') as 'open' | 'closed'),
    message: toString(a.message ?? a.title, ''),
    createdAt: toString(a.createdAt ?? a.created_at ?? a.timestamp),
    source: toString(a.source ?? a.component, ''),
  }));
}

export function normalizeJobs(input: any) {
  return getArray<any>(input).map((j, idx) => ({
    id: toString(j.id ?? j.name ?? j.job_name, `job-${idx}`),
    name: toString(j.name ?? j.job_name, `job-${idx}`),
    nextRun: toString(j.nextRun ?? j.next_run),
    lastRun: toString(j.lastRun ?? j.last_run),
    status: normalizeStatus(j.status, 'idle') as 'running' | 'idle' | 'failed' | 'paused',
    durationMs: toNumber(j.durationMs ?? j.duration_ms),
  }));
}

export function normalizeStrategies(input: any) {
  return getArray<any>(input).map((s, idx) => ({
    id: toString(s.id ?? s.strategy_id ?? s.name, `strategy-${idx}`),
    name: toString(s.name ?? s.strategy_name, `Strategy ${idx + 1}`),
    mode: (toString(s.mode, 'paper') as 'paper' | 'shadow' | 'live'),
    status: (toString(s.status, 'running') as 'running' | 'paused' | 'stopped'),
    capitalPct: toNumber(s.capitalPct ?? s.capital_pct ?? s.capitalAllocation ?? s.capital_allocation),
    riskBudget: toNumber(s.riskBudget ?? s.risk_budget),
    pnl: toNumber(s.pnl),
    capitalAllocation: toNumber(s.capitalAllocation ?? s.capital_allocation ?? s.capitalPct ?? s.capital_pct),
  }));
}

export function normalizeApprovals(input: any) {
  return getArray<any>(input).map((a, idx) => ({
    id: toString(a.id ?? a.approval_id, `approval-${idx}`),
    alphaId: toString(a.alphaId ?? a.alpha_id ?? a.target, ''),
    status: (toString(a.status, 'pending') as 'pending' | 'approved' | 'rejected'),
    sharpe: toNumber(a.sharpe),
    updatedAt: toString(a.updatedAt ?? a.updated_at ?? a.createdAt ?? a.created_at),
    target: toString(a.target ?? a.alphaId ?? a.alpha_id, ''),
  }));
}

export function normalizeConfig(input: any) {
  const x = getPayload<any>(input, {});
  return {
    version: toString(x.version, 'local-default'),
    schedulerCadenceSec: toNumber(x.schedulerCadenceSec ?? x.scheduler_cadence_sec ?? x.schedulerIntervalSec ?? x.scheduler_interval_sec, 60),
    riskLimit: toNumber(x.riskLimit ?? x.risk_limit, 0.1),
    monitoringThreshold: toNumber(x.monitoringThreshold ?? x.monitoring_threshold, 0.9),
    executionMode: (toString(x.executionMode ?? x.execution_mode, 'paper') as 'paper' | 'shadow' | 'live'),
    environment: toString(x.environment, ''),
    riskLimits: x.riskLimits ?? x.risk_limits ?? {},
    schedulerCadence: x.schedulerCadence ?? x.scheduler_cadence ?? {},
    monitoringThresholds: x.monitoringThresholds ?? x.monitoring_thresholds ?? {},
  };
}

export function normalizeCurrentUser(input: any) {
  const x = getPayload<any>(input, {});
  return {
    id: toString(x.id, 'local-viewer'),
    name: toString(x.name, 'Local Viewer'),
    role: (toString(x.role, 'viewer') as 'viewer' | 'operator' | 'risk_manager' | 'admin'),
  };
}

export function normalizeAuditLogs(input: any) {
  return getArray<any>(input).map((a, idx) => ({
    id: toString(a.id, `audit-${idx}`),
    actor: toString(a.actor, ''),
    role: (toString(a.role, 'viewer') as 'viewer' | 'operator' | 'risk_manager' | 'admin'),
    action: toString(a.action, ''),
    target: toString(a.target, ''),
    timestamp: toString(a.timestamp ?? a.createdAt ?? a.created_at),
    status: (toString(a.status, 'success') as 'success' | 'denied' | 'failed'),
    detail: toString(a.detail ?? a.details, ''),
    createdAt: toString(a.createdAt ?? a.created_at ?? a.timestamp),
    details: toString(a.details ?? a.detail, ''),
  }));
}

export function normalizeEquityHistory(input: any) {
  const items = getArray<any>(input).length ? getArray<any>(input) : getArray<any>(getPayload<any>(input, {}).items);
  const payload = getPayload<any>(input, {});
  const source = items.length ? items : Array.isArray(payload.items) ? payload.items : [];
  return source.map((row: any, idx: number) => ({
    name: toString(row.name ?? row.label ?? row.as_of ?? row.asOf, `pt-${idx}`),
    value: toNumber(row.value ?? row.equity ?? row.total_equity ?? row.totalEquity),
    pnl: toNumber(row.pnl ?? row.total_pnl ?? row.totalPnl),
    asOf: toString(row.asOf ?? row.as_of ?? row.name, ''),
  }));
}

export function normalizeExecutionSummary(input: any) {
  const x = getPayload<any>(input, {});
  return {
    fillRate: toNumber(x.fillRate ?? x.fill_rate),
    avgSlippageBps: toNumber(x.avgSlippageBps ?? x.avg_slippage_bps),
    latencyMsP50: toNumber(x.latencyMsP50 ?? x.latency_ms_p50),
    latencyMsP95: toNumber(x.latencyMsP95 ?? x.latency_ms_p95),
    venueScore: toNumber(x.venueScore ?? x.venue_score),
    asOf: toString(x.asOf ?? x.as_of),
  };
}


export function normalizeExecutionPlannerLatest(input: any) {
  const x = getPayload<any>(input, {});
  const rows = Array.isArray(x.items) ? x.items : [];
  return {
    tradingState: toString(x.tradingState ?? x.trading_state, 'unknown'),
    planCount: toNumber(x.planCount ?? x.plan_count),
    expiredCount: toNumber(x.expiredCount ?? x.expired_count),
    asOf: toString(x.asOf ?? x.as_of),
    algoMix: x.algoMix ?? x.algo_mix ?? {},
    routeMix: x.routeMix ?? x.route_mix ?? {},
    items: rows.map((r: any, idx: number) => ({
      planId: toString(r.planId ?? r.plan_id, `plan-${idx}`),
      symbol: toString(r.symbol, `plan-${idx}`),
      side: toString(r.side, ''),
      algo: toString(r.algo, ''),
      route: toString(r.route, ''),
      sliceCount: toNumber(r.sliceCount ?? r.slice_count),
      expireSeconds: toNumber(r.expireSeconds ?? r.expire_seconds),
      effectiveStatus: toString(r.effectiveStatus ?? r.effective_status ?? r.status, ''),
      createdAt: toString(r.createdAt ?? r.created_at, ''),
      planAgeSec: toNumber(r.planAgeSec ?? r.plan_age_sec),
      lastExecutionAt: toString(r.lastExecutionAt ?? r.last_execution_at, ''),
      lastExecutionAgeSec: toNumber(r.lastExecutionAgeSec ?? r.last_execution_age_sec),
      orderCount: toNumber(r.orderCount ?? r.order_count),
      fillCount: toNumber(r.fillCount ?? r.fill_count),
      active: Boolean(r.active),
      activityState: toString(r.activityState ?? r.activity_state, ''),
    })),
    visiblePlanCount: toNumber(x.visiblePlanCount ?? x.visible_plan_count),
    latestActivityAt: toString(x.latestActivityAt ?? x.latest_activity_at),
  };
}

export function normalizeExecutionFills(input: any) {
  const payload = getPayload<any>(input, {});
  const rows = Array.isArray(payload.items) ? payload.items : getArray<any>(input);
  return rows.map((r: any, idx: number) => ({
    fillId: toString(r.fillId ?? r.fill_id, `fill-${idx}`),
    symbol: toString(r.symbol, `fill-${idx}`),
    side: toString(r.side, ''),
    fillQty: toNumber(r.fillQty ?? r.fill_qty),
    fillPrice: toNumber(r.fillPrice ?? r.fill_price),
    slippageBps: toNumber(r.slippageBps ?? r.slippage_bps),
    latencyMs: toNumber(r.latencyMs ?? r.latency_ms),
    feeBps: toNumber(r.feeBps ?? r.fee_bps),
    status: toString(r.status, ''),
  }));
}

export function normalizeExecutionOrders(input: any) {
  const payload = getPayload<any>(input, {});
  const rows = Array.isArray(payload.items) ? payload.items : getArray<any>(input);
  return rows.map((r: any, idx: number) => ({
    orderId: toString(r.orderId ?? r.order_id, `order-${idx}`),
    planId: toString(r.planId ?? r.plan_id, ''),
    symbol: toString(r.symbol, `order-${idx}`),
    side: toString(r.side, ''),
    qty: toNumber(r.qty),
    venue: toString(r.venue, ''),
    algo: toString(r.algo, ''),
    route: toString(r.route, ''),
    status: toString(r.status, ''),
    submitTime: toString(r.submitTime ?? r.submit_time ?? r.createdAt ?? r.created_at, ''),
  }));
}

export function normalizeExecutionState(input: any) {
  const x = getPayload<any>(input, {});
  const reasons = Array.isArray(x.blockReasons) ? x.blockReasons : Array.isArray(x.block_reasons) ? x.block_reasons : [];
  return {
    tradingState: toString(x.tradingState ?? x.trading_state, 'unknown'),
    executionState: toString(x.executionState ?? x.execution_state, 'unknown'),
    reason: toString(x.reason, ''),
    plannerAgeSec: toNumber(x.plannerAgeSec ?? x.planner_age_sec),
    executionAgeSec: toNumber(x.executionAgeSec ?? x.execution_age_sec),
    lastFillAgeSec: toNumber(x.lastFillAgeSec ?? x.last_fill_age_sec),
    openOrderCount: toNumber(x.openOrderCount ?? x.open_order_count),
    activePlanCount: toNumber(x.activePlanCount ?? x.active_plan_count),
    visiblePlanCount: toNumber(x.visiblePlanCount ?? x.visible_plan_count),
    expiredPlanCount: toNumber(x.expiredPlanCount ?? x.expired_plan_count),
    submittedOrderCount: toNumber(x.submittedOrderCount ?? x.submitted_order_count),
    asOf: toString(x.asOf ?? x.as_of),
    blockReasons: reasons.map((item: any) => ({ code: toString(item.code), severity: toString(item.severity), message: toString(item.message) })),
  };
}

export function normalizeCommandCenterRuntimeLatest(input: any): CommandCenterRuntimeLatest {
  const x = getPayload<any>(input, {});
  const timeline = Array.isArray(x.timeline) ? x.timeline : [];
  return {
    status: toString(x.status, 'no_data'),
    runId: toString(x.runId ?? x.run_id, ''),
    cycleId: toString(x.cycleId ?? x.cycle_id, ''),
    bridgeState: toString(x.bridgeState ?? x.bridge_state, 'no_decision'),
    operatorState: toString(x.operatorState ?? x.operator_state ?? x.bridgeState ?? x.bridge_state, 'no_decision'),
    plannerStatus: toString(x.plannerStatus ?? x.planner_status, 'unknown'),
    plannedCount: toNumber(x.plannedCount ?? x.planned_count),
    submittedCount: toNumber(x.submittedCount ?? x.submitted_count),
    blockedCount: toNumber(x.blockedCount ?? x.blocked_count),
    filledCount: toNumber(x.filledCount ?? x.filled_count),
    eventChainComplete: toBool(x.eventChainComplete ?? x.event_chain_complete, false),
    latestReasonCode: toString(x.latestReasonCode ?? x.latest_reason_code, ''),
    latestReasonSummary: toString(x.latestReasonSummary ?? x.latest_reason_summary, ''),
    blockingComponent: toString(x.blockingComponent ?? x.blocking_component, ''),
    degraded: toBool(x.degraded, Array.isArray(x.degradedFlags ?? x.degraded_flags) && (x.degradedFlags ?? x.degraded_flags).length > 0),
    degradedFlags: Array.isArray(x.degradedFlags ?? x.degraded_flags) ? (x.degradedFlags ?? x.degraded_flags) : [],
    operatorMessage: toString(x.operatorMessage ?? x.operator_message, ''),
    generatedAt: toString(x.generatedAt ?? x.generated_at, ''),
    lastTransitionAt: toString(x.lastTransitionAt ?? x.last_transition_at, ''),
    lastSuccessfulFillAt: toString(x.lastSuccessfulFillAt ?? x.last_successful_fill_at, ''),
    lastSuccessfulPortfolioUpdateAt: toString(x.lastSuccessfulPortfolioUpdateAt ?? x.last_successful_portfolio_update_at, ''),
    lastCycleCompletedAt: toString(x.lastCycleCompletedAt ?? x.last_cycle_completed_at, ''),
    debugPath: toString(x.debugPath ?? x.debug_path, ''),
    detailPath: toString(x.detailPath ?? x.detail_path, ''),
    timeline: timeline.map((item: any) => ({
      eventType: toString(item.eventType ?? item.event_type, ''),
      summary: toString(item.summary, ''),
      severity: toString(item.severity, 'info'),
      status: toString(item.status, 'ok'),
      reasonCode: toString(item.reasonCode ?? item.reason_code, ''),
      symbol: toString(item.symbol, ''),
      timestamp: toString(item.timestamp ?? item.created_at, ''),
    })),
  };
}

export function normalizeCommandCenterRuntimeDebug(input: any): CommandCenterRuntimeDebug {
  const x = getPayload<any>(input, {});
  const summary = getPayload<any>(x.summary, {});
  const timeline = Array.isArray(x.timeline) ? x.timeline : [];
  return {
    scope: toString(x.scope, 'command_center.runtime'),
    status: toString(x.status, 'no_data'),
    source: toString(x.source, 'unknown'),
    reason: toString(x.reason, ''),
    asOf: toString(x.asOf ?? x.as_of, ''),
    timings: {
      snapshotAgeSec: toNumber(x.timings?.snapshot_age_sec ?? x.timings?.snapshotAgeSec),
    },
    summary: {
      runId: toString(summary.runId ?? summary.run_id, ''),
      cycleId: toString(summary.cycleId ?? summary.cycle_id, ''),
      bridgeState: toString(summary.bridgeState ?? summary.bridge_state, ''),
      operatorState: toString(summary.operatorState ?? summary.operator_state, ''),
      plannerStatus: toString(summary.plannerStatus ?? summary.planner_status, ''),
      plannedCount: toNumber(summary.plannedCount ?? summary.planned_count),
      submittedCount: toNumber(summary.submittedCount ?? summary.submitted_count),
      blockedCount: toNumber(summary.blockedCount ?? summary.blocked_count),
      filledCount: toNumber(summary.filledCount ?? summary.filled_count),
      eventChainComplete: toBool(summary.eventChainComplete ?? summary.event_chain_complete, false),
      latestReasonCode: toString(summary.latestReasonCode ?? summary.latest_reason_code, ''),
      latestReasonSummary: toString(summary.latestReasonSummary ?? summary.latest_reason_summary, ''),
      blockingComponent: toString(summary.blockingComponent ?? summary.blocking_component, ''),
      operatorMessage: toString(summary.operatorMessage ?? summary.operator_message, ''),
      degraded: toBool(summary.degraded, false),
      degradedFlags: Array.isArray(summary.degradedFlags ?? summary.degraded_flags) ? (summary.degradedFlags ?? summary.degraded_flags) : [],
      lastSuccessfulFillAt: toString(summary.lastSuccessfulFillAt ?? summary.last_successful_fill_at, ''),
      lastSuccessfulPortfolioUpdateAt: toString(summary.lastSuccessfulPortfolioUpdateAt ?? summary.last_successful_portfolio_update_at, ''),
      lastCycleCompletedAt: toString(summary.lastCycleCompletedAt ?? summary.last_cycle_completed_at, ''),
    },
    provenance: {
      ...(x.provenance ?? {}),
      artifactBundle: x.provenance?.artifact_bundle
        ? {
            runId: toString(x.provenance.artifact_bundle.run_id, ''),
            path: toString(x.provenance.artifact_bundle.path, ''),
            name: toString(x.provenance.artifact_bundle.name, ''),
          }
        : undefined,
    },
    counts: x.counts ?? {},
    timeline: timeline.map((item: any) => ({
      eventType: toString(item.eventType ?? item.event_type, ''),
      summary: toString(item.summary, ''),
      severity: toString(item.severity, 'info'),
      status: toString(item.status, 'ok'),
      reasonCode: toString(item.reasonCode ?? item.reason_code, ''),
      symbol: toString(item.symbol, ''),
      timestamp: toString(item.timestamp ?? item.created_at, ''),
    })),
    raw: {
      planner: x.raw?.planner ?? {},
      bridge: x.raw?.bridge ?? {},
      events: Array.isArray(x.raw?.events) ? x.raw.events : [],
      reasons: Array.isArray(x.raw?.reasons) ? x.raw.reasons : [],
    },
  };
}

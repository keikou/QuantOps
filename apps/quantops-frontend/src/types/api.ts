export type ApiSource = 'live' | 'mock';
export type DataStatus = 'ok' | 'loading' | 'stale' | 'timed_out' | 'no_data' | 'fallback';
export type DataSourceStatus = 'live' | 'cache' | 'empty' | 'fallback' | 'unknown';

export type ApiEnvelope<T> = {
  data: T;
  source: ApiSource;
};

export type ActionResult = {
  ok: boolean;
  message: string;
};

export type OverviewData = {
  totalEquity: number;
  balance: number;
  usedMargin: number;
  freeMargin: number;
  unrealized: number;
  asOf?: string;
  dailyPnl: number;
  grossExposure: number;
  netExposure: number;
  activeStrategies: number;
  openAlerts: number;
  runningJobs: number;
  pnlSeries: Array<{ name: string; value: number }>;
  executionState?: string;
  executionReason?: string;
  workerStatus?: string;
  riskTradingState?: string;
  killSwitch?: string;
  alertState?: string;
};

export type PortfolioOverview = {
  totalEquity: number;
  balance: number;
  usedMargin: number;
  freeMargin: number;
  unrealized: number;
  grossExposure: number;
  netExposure: number;
  realizedPnl: number;
  unrealizedPnl: number;
  expectedVolatility: number;
  expectedSharpe: number;
  lastUpdated: string;
};

export type PositionRow = {
  symbol: string;
  side: 'long' | 'short';
  quantity: number;
  avgPrice: number;
  markPrice: number;
  pnl: number;
  strategyId?: string;
  alphaFamily?: string;
};

export type RiskSnapshot = {
  grossExposure: number;
  netExposure: number;
  var1d: number;
  drawdown: number;
  concentration: number;
  killSwitch: 'normal' | 'armed' | 'triggered';
  tradingState?: 'running' | 'paused';
  alert?: string;
  dataStatus?: DataStatus;
  dataSource?: DataSourceStatus;
  statusReason?: string;
  isStale?: boolean;
  asOf?: string;
};

export type MonitoringSystem = {
  cpu: number;
  memory: number;
  disk: string;
  dbWritable: boolean;
  exchangeLatencyMs: number;
  dataFreshnessSec: number;
  exchange?: string;
  latencyMs?: number;
  queue?: number;
  workerStatus?: string;
  executionState?: string;
  executionReason?: string;
  riskTradingState?: string;
  killSwitch?: string;
  alertState?: string;
  dataStatus?: DataStatus;
  dataSource?: DataSourceStatus;
  statusReason?: string;
  isStale?: boolean;
  asOf?: string;
};

export type AlertRow = {
  id: string;
  severity: 'info' | 'warning' | 'critical';
  status: 'open' | 'closed' | 'acknowledged' | 'resolved';
  message: string;
  createdAt: string;
};

export type JobRow = {
  name: string;
  nextRun: string;
  lastRun: string;
  status: 'running' | 'idle' | 'failed' | 'paused';
  durationMs: number;
};

export type StrategyRow = {
  id: string;
  name: string;
  mode: 'paper' | 'shadow' | 'live';
  status: 'running' | 'paused' | 'stopped';
  capitalPct: number;
  riskBudget: number;
  pnl: number;
};

export type GovernanceDecision = {
  id: string;
  alphaId: string;
  status: 'pending' | 'approved' | 'rejected';
  sharpe: number;
  updatedAt: string;
};

export type ConfigDraft = {
  version: string;
  schedulerCadenceSec: number;
  riskLimit: number;
  monitoringThreshold: number;
  executionMode: 'paper' | 'shadow' | 'live';
};

export type UserRole = 'viewer' | 'operator' | 'risk_manager' | 'admin';

export type CurrentUser = {
  id: string;
  name: string;
  role: UserRole;
};

export type AuditLogRow = {
  id: string;
  actor: string;
  role: UserRole;
  action: string;
  target: string;
  timestamp: string;
  status: 'success' | 'denied' | 'failed';
  detail?: string;
};

export type CommandCenterRealtimeEvent = {
  event_type: 'hello' | 'heartbeat' | 'pnl_update' | 'execution_event' | 'risk_alert' | 'strategy_status' | 'system_status';
  as_of: string;
  payload: Record<string, unknown>;
};

export type EquityPoint = {
  name: string;
  value: number;
  pnl?: number;
  asOf?: string;
};

export type ExecutionSummary = {
  fillRate: number;
  avgSlippageBps: number;
  latencyMsP50: number;
  latencyMsP95: number;
  venueScore: number;
  asOf: string;
};

export type ExecutionFillRow = {
  fillId?: string;
  symbol: string;
  side?: string;
  fillQty?: number;
  fillPrice?: number;
  slippageBps?: number;
  latencyMs?: number;
  feeBps?: number;
  status?: string;
};


export type ExecutionPlannerItem = {
  planId?: string;
  symbol: string;
  side?: string;
  algo?: string;
  route?: string;
  sliceCount?: number;
  expireSeconds?: number;
  effectiveStatus?: string;
  createdAt?: string;
  planAgeSec?: number;
  lastExecutionAt?: string;
  lastExecutionAgeSec?: number;
  orderCount?: number;
  fillCount?: number;
  active?: boolean;
  activityState?: string;
};

export type ExecutionPlannerLatest = {
  tradingState: string;
  planCount: number;
  visiblePlanCount?: number;
  expiredCount: number;
  asOf: string;
  latestActivityAt?: string;
  algoMix: Record<string, number>;
  routeMix: Record<string, number>;
  items: ExecutionPlannerItem[];
};

export type ExecutionOrderRow = {
  orderId?: string;
  planId?: string;
  symbol: string;
  side?: string;
  qty?: number;
  venue?: string;
  algo?: string;
  route?: string;
  status?: string;
  submitTime?: string;
};

export type ExecutionState = {
  tradingState: string;
  executionState: string;
  reason?: string;
  plannerAgeSec?: number;
  executionAgeSec?: number;
  lastFillAgeSec?: number;
  openOrderCount?: number;
  activePlanCount?: number;
  visiblePlanCount?: number;
  expiredPlanCount?: number;
  submittedOrderCount?: number;
  asOf: string;
  blockReasons?: Array<{ code: string; severity?: string; message?: string }>;
};

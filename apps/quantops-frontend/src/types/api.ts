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
  buildStatus?: string;
  sourceSnapshotTime?: string;
  dataFreshnessSec?: number;
  activeSnapshotVersion?: number;
  positionRowCount?: number;
  strategyRowCount?: number;
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
  buildStatus?: string;
  sourceSnapshotTime?: string;
  dataFreshnessSec?: number;
  lastUpdated: string;
};

export type PortfolioMetrics = {
  fillRate: number;
  expectedVolatility: number;
  expectedSharpe: number;
  buildStatus?: string;
  sourceSnapshotTime?: string;
  dataFreshnessSec?: number;
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
  event_type: 'hello' | 'heartbeat' | 'pnl_update' | 'execution_event' | 'risk_alert' | 'strategy_status' | 'system_status' | 'runtime_run' | 'runtime_issue';
  as_of: string;
  payload: Record<string, unknown>;
};

export type EquityPoint = {
  name: string;
  value: number;
  pnl?: number;
  asOf?: string;
};

export type PositionFeed = FeedPayload<PositionRow>;
export type EquityHistoryFeed = FeedPayload<EquityPoint>;

export type FeedPayload<T> = {
  items: T[];
  asOf?: string;
  buildStatus?: string;
  sourceSnapshotTime?: string;
  dataFreshnessSec?: number;
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
  buildStatus?: string;
  sourceSnapshotTime?: string;
  dataFreshnessSec?: number;
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
  buildStatus?: string;
  sourceSnapshotTime?: string;
  dataFreshnessSec?: number;
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

export type ExecutionViewLatest = {
  planner: ExecutionPlannerLatest;
  state: ExecutionState;
  stableValue?: {
    tradingState?: string;
    executionState?: string;
    reason?: string;
    primaryReason?: string;
    plannerAgeSec?: number;
    executionAgeSec?: number;
    lastFillAgeSec?: number;
    openOrderCount?: number;
    submittedOrderCount?: number;
    activePlanCount?: number;
    visiblePlanCount?: number;
    expiredPlanCount?: number;
    topAlgo?: string;
    topRoute?: string;
  };
  liveDelta?: {
    recentFillsWindow?: number | null;
    recentOrdersWindow?: number | null;
    recentRunsWindow?: number | null;
    recentIssuesWindow?: number | null;
  };
  displayValue?: {
    tradingState?: string;
    executionState?: string;
    reason?: string;
    primaryReason?: string;
    plannerAgeSec?: number;
    executionAgeSec?: number;
    lastFillAgeSec?: number;
    openOrderCount?: number;
    submittedOrderCount?: number;
    activePlanCount?: number;
    visiblePlanCount?: number;
    expiredPlanCount?: number;
    topAlgo?: string;
    topRoute?: string;
  };
  asOf: string;
  buildStatus?: string;
  sourceSnapshotTime?: string;
  dataFreshnessSec?: number;
};

export type RuntimeTimelineEvent = {
  eventType: string;
  summary: string;
  severity: string;
  status: string;
  reasonCode?: string;
  symbol?: string;
  timestamp: string;
};

export type RuntimeStage = {
  key: string;
  title: string;
  state: string;
  timestamp?: string;
  summary: string;
  reasonCode?: string;
  evidence: string[];
};

export type RuntimeDiagnosis = {
  primaryCode: string;
  secondaryCodes: string[];
  severity: string;
  retryability: string;
  operatorAction: string;
  likelyComponent: string;
  confidence: number;
  summary?: string;
};

export type RuntimeIssueBucket = {
  code: string;
  count: number;
  distinctRunCount: number;
  severity: string;
  retryability: string;
  operatorAction: string;
  likelyComponent: string;
  firstSeenAt?: string;
  latestSeenAt?: string;
  exampleRunId?: string;
  recurrenceStatus: string;
  trend: string;
  windowRunCount: number;
  windowStart?: string;
  windowEnd?: string;
};

export type CommandCenterRuntimeLatest = {
  status: string;
  runId?: string;
  cycleId?: string;
  buildStatus?: string;
  sourceSnapshotTime?: string;
  dataFreshnessSec?: number;
  bridgeState: string;
  operatorState: string;
  plannerStatus: string;
  plannedCount: number;
  submittedCount: number;
  blockedCount: number;
  filledCount: number;
  eventChainComplete: boolean;
  latestReasonCode?: string;
  latestReasonSummary?: string;
  blockingComponent?: string;
  degraded: boolean;
  degradedFlags: string[];
  operatorMessage?: string;
  generatedAt?: string;
  lastTransitionAt?: string;
  lastSuccessfulFillAt?: string;
  lastSuccessfulPortfolioUpdateAt?: string;
  lastCycleCompletedAt?: string;
  debugPath?: string;
  detailPath?: string;
  timeline: RuntimeTimelineEvent[];
};

export type CommandCenterRuntimeRunSummary = {
  runId: string;
  cycleId?: string;
  status: string;
  startedAt?: string;
  completedAt?: string;
  durationMs?: number;
  triggeredBy?: string;
  bridgeState: string;
  operatorState: string;
  plannerStatus: string;
  plannedCount: number;
  submittedCount: number;
  blockedCount: number;
  filledCount: number;
  eventChainComplete: boolean;
  latestReasonCode?: string;
  latestReasonSummary?: string;
  blockingComponent?: string;
  degraded: boolean;
  degradedFlags: string[];
  lastSuccessfulFillAt?: string;
  detailPath?: string;
  artifactAvailable: boolean;
  diagnosis?: RuntimeDiagnosis;
  diagnosisCode?: string;
};

export type CommandCenterRuntimeDebug = {
  scope: string;
  status: string;
  source: string;
  reason?: string;
  asOf?: string;
  timings?: { snapshotAgeSec?: number };
  run?: {
    runId?: string;
    status?: string;
    jobName?: string;
    mode?: string;
    triggeredBy?: string;
    startedAt?: string;
    finishedAt?: string;
    durationMs?: number;
    errorMessage?: string;
  };
  summary: {
    runId?: string;
    cycleId?: string;
    bridgeState?: string;
    operatorState?: string;
    plannerStatus?: string;
    plannedCount?: number;
    submittedCount?: number;
    blockedCount?: number;
    filledCount?: number;
    eventChainComplete?: boolean;
    latestReasonCode?: string;
    latestReasonSummary?: string;
    blockingComponent?: string;
    operatorMessage?: string;
    degraded?: boolean;
    degradedFlags?: string[];
    lastSuccessfulFillAt?: string;
    lastSuccessfulPortfolioUpdateAt?: string;
    lastCycleCompletedAt?: string;
  };
  provenance?: Record<string, unknown> & {
    artifactBundle?: {
      runId?: string;
      path?: string;
      name?: string;
    };
  };
  artifacts?: {
    bundle?: {
      runId?: string;
      path?: string;
      name?: string;
    };
    checkpointCount?: number;
    auditLogCount?: number;
    available?: string[];
    missing?: string[];
  };
  diagnosis?: RuntimeDiagnosis;
  diagnosisContext?: {
    seenInRecentRuns?: string;
    recurrenceStatus?: string;
    trend?: string;
    firstSeenAt?: string;
    lastSeenAt?: string;
  };
  counts?: Record<string, number>;
  stages: RuntimeStage[];
  timeline: RuntimeTimelineEvent[];
  raw: {
    run?: Record<string, unknown>;
    planner?: Record<string, unknown>;
    bridge?: Record<string, unknown>;
    events?: Array<Record<string, unknown>>;
    reasons?: Array<Record<string, unknown>>;
  };
};

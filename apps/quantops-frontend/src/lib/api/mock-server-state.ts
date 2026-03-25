import type {
  ActionResult,
  AlertRow,
  ApiEnvelope,
  ConfigDraft,
  GovernanceDecision,
  JobRow,
  MonitoringSystem,
  OverviewData,
  PortfolioMetrics,
  PortfolioOverview,
  PositionRow,
  RiskSnapshot,
  StrategyRow,
  CurrentUser,
  AuditLogRow,
} from '@/types/api';

const nowIso = () => new Date().toISOString();

const state = {
  currentUser: { id: 'u-1', name: 'Operator Demo', role: 'admin' } as CurrentUser,
  overview: {
    totalEquity: 1052340,
    dailyPnl: 12034,
    grossExposure: 1.82,
    netExposure: 0.34,
    activeStrategies: 3,
    openAlerts: 2,
    runningJobs: 4,
    pnlSeries: [
      { name: 'Mon', value: 1010000 },
      { name: 'Tue', value: 1019000 },
      { name: 'Wed', value: 1025000 },
      { name: 'Thu', value: 1037000 },
      { name: 'Fri', value: 1052340 },
    ],
  } as OverviewData,
  portfolioOverview: {
    totalEquity: 1052340,
    balance: 996800,
    usedMargin: 42100,
    freeMargin: 1010240,
    unrealized: 43440,
    grossExposure: 1.82,
    netExposure: 0.34,
    realizedPnl: 12034,
    unrealizedPnl: 4201,
    lastUpdated: nowIso(),
  } as PortfolioOverview,
  portfolioMetrics: {
    fillRate: 0.97,
    expectedVolatility: 0.18,
    expectedSharpe: 1.92,
    lastUpdated: nowIso(),
  } as PortfolioMetrics,
  positions: [
    { symbol: 'BTCUSDT', side: 'long', quantity: 1.2, avgPrice: 43000, markPrice: 44120, pnl: 1340, strategyId: 'momentum', alphaFamily: 'momentum' },
    { symbol: 'ETHUSDT', side: 'short', quantity: 5, avgPrice: 3200, markPrice: 3150, pnl: 250, strategyId: 'meanrev', alphaFamily: 'mean_reversion' },
    { symbol: 'SOLUSDT', side: 'long', quantity: 80, avgPrice: 90, markPrice: 92, pnl: 160, strategyId: 'statarb', alphaFamily: 'stat_arb' },
  ] as PositionRow[],
  risk: {
    grossExposure: 1.82,
    netExposure: 0.34,
    var1d: -1.8,
    drawdown: -3.2,
    concentration: 12,
    killSwitch: 'normal',
  } as RiskSnapshot,
  monitoring: {
    cpu: 32,
    memory: 41,
    disk: 'OK',
    dbWritable: true,
    exchangeLatencyMs: 32,
    dataFreshnessSec: 4,
  } as MonitoringSystem,
  alerts: [
    { id: 'alert-1', severity: 'warning', status: 'open', message: 'Exchange latency spike', createdAt: nowIso() },
    { id: 'alert-2', severity: 'critical', status: 'open', message: 'Risk threshold breach', createdAt: nowIso() },
    { id: 'alert-3', severity: 'info', status: 'closed', message: 'Daily pnl report generated', createdAt: nowIso() },
  ] as AlertRow[],
  jobs: [
    { name: 'system_health', nextRun: '30s', lastRun: 'ok', status: 'running', durationMs: 122 },
    { name: 'exchange_health', nextRun: '60s', lastRun: 'ok', status: 'running', durationMs: 188 },
    { name: 'portfolio_rebalance', nextRun: '15m', lastRun: 'ok', status: 'idle', durationMs: 812 },
    { name: 'alpha_factory', nextRun: '1h', lastRun: 'ok', status: 'paused', durationMs: 1302 },
  ] as JobRow[],
  strategies: [
    { id: 'momentum', name: 'Momentum', mode: 'paper', status: 'running', capitalPct: 20, riskBudget: 0.12, pnl: 1320 },
    { id: 'meanrev', name: 'Mean Reversion', mode: 'shadow', status: 'running', capitalPct: 15, riskBudget: 0.1, pnl: 420 },
    { id: 'statarb', name: 'Stat Arb', mode: 'paper', status: 'paused', capitalPct: 10, riskBudget: 0.08, pnl: -30 },
  ] as StrategyRow[],
  governance: [
    { id: 'gov-1', alphaId: 'alpha_241', status: 'pending', sharpe: 2.2, updatedAt: nowIso() },
    { id: 'gov-2', alphaId: 'alpha_233', status: 'pending', sharpe: 1.8, updatedAt: nowIso() },
  ] as GovernanceDecision[],
  config: {
    version: 'draft-2026-03-16-01',
    schedulerCadenceSec: 60,
    riskLimit: 0.1,
    monitoringThreshold: 0.9,
    executionMode: 'paper',
  } as ConfigDraft,
  auditLogs: [
    { id: 'audit-1', actor: 'Operator Demo', role: 'admin', action: 'login', target: 'quantops', timestamp: nowIso(), status: 'success', detail: 'demo session started' },
  ] as AuditLogRow[],
};

const wrap = <T,>(data: T): ApiEnvelope<T> => ({ data, source: 'mock' });
const result = (message: string): ApiEnvelope<ActionResult> => ({ data: { ok: true, message }, source: 'mock' });

function appendAudit(action: string, target: string, status: 'success' | 'denied' | 'failed' = 'success', detail?: string) {
  state.auditLogs = [{
    id: `audit-${Date.now()}`,
    actor: state.currentUser.name,
    role: state.currentUser.role,
    action,
    target,
    timestamp: nowIso(),
    status,
    detail,
  }, ...state.auditLogs].slice(0, 50);
}

export function getMockResponse(path: string): ApiEnvelope<unknown> | undefined {
  if (path === '/api/v1/auth/me') return wrap(state.currentUser);
  if (path === '/api/v1/dashboard/overview') return wrap(state.overview);
  if (path === '/api/v1/portfolio/overview') return wrap({ ...state.portfolioOverview, lastUpdated: nowIso() });
  if (path === '/api/v1/portfolio/metrics') return wrap({ ...state.portfolioMetrics, lastUpdated: nowIso() });
  if (path === '/api/v1/portfolio/positions') return wrap(state.positions);
  if (path === '/api/v1/risk/snapshot') return wrap(state.risk);
  if (path === '/api/v1/monitoring/system') return wrap(state.monitoring);
  if (path === '/api/v1/alerts') return wrap(state.alerts);
  if (path === '/api/v1/scheduler/jobs') return wrap(state.jobs);
  if (path === '/api/v1/strategy/registry') return wrap(state.strategies);
  if (path === '/api/v1/governance/approvals') return wrap(state.governance);
  if (path === '/api/v1/config/current') return wrap(state.config);
  if (path === '/api/v1/admin/audit-logs') return wrap(state.auditLogs);
  return undefined;
}

export async function applyMockMutation(path: string, body?: unknown): Promise<ApiEnvelope<ActionResult> | undefined> {
  const matchAlertAck = path.match(/^\/api\/v1\/alerts\/([^/]+)\/acknowledge$/);
  if (matchAlertAck) {
    state.alerts = state.alerts.map((a) => a.id === matchAlertAck[1] ? { ...a, status: 'closed' } : a);
    state.overview.openAlerts = state.alerts.filter((a) => a.status === 'open').length;
    appendAudit('alerts.acknowledge', matchAlertAck[1]);
    return result(`Alert ${matchAlertAck[1]} acknowledged`);
  }

  const jobAction = path.match(/^\/api\/v1\/scheduler\/jobs\/([^/]+)\/(run|pause|resume)$/);
  if (jobAction) {
    const [, name, action] = jobAction;
    state.jobs = state.jobs.map((j) => j.name === name ? {
      ...j,
      status: action === 'pause' ? 'paused' : action === 'resume' ? 'running' : 'running',
      lastRun: action === 'run' ? nowIso() : j.lastRun,
    } : j);
    appendAudit(`scheduler.${action}`, name);
    return result(`Job ${name} ${action} executed`);
  }

  const strategyAction = path.match(/^\/api\/v1\/strategy\/([^/]+)\/(start|stop)$/);
  if (strategyAction) {
    const [, id, action] = strategyAction;
    state.strategies = state.strategies.map((s) => s.id === id ? { ...s, status: action === 'start' ? 'running' : 'stopped' } : s);
    state.overview.activeStrategies = state.strategies.filter((s) => s.status === 'running').length;
    appendAudit(`strategy.${action}`, id);
    return result(`Strategy ${id} ${action} executed`);
  }

  const govAction = path.match(/^\/api\/v1\/governance\/approvals\/([^/]+)\/(approve|reject)$/);
  if (govAction) {
    const [, id, action] = govAction;
    state.governance = state.governance.map((g) => g.id === id ? { ...g, status: action === 'approve' ? 'approved' : 'rejected', updatedAt: nowIso() } : g);
    appendAudit(`governance.${action}`, id);
    return result(`Governance ${id} ${action}d`);
  }

  if (path === '/api/v1/config/draft/save') {
    const next = typeof body === 'object' && body ? body as Partial<ConfigDraft> : {};
    state.config = { ...state.config, ...next, version: `draft-${Date.now()}` };
    appendAudit('config.draft.save', state.config.version);
    return result('Config draft saved');
  }

  return undefined;
}

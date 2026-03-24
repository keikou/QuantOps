import type { AlertRow, ApiEnvelope, JobRow, MonitoringSystem, OverviewData, PortfolioOverview, PositionRow, RiskSnapshot } from '@/types/api';

export const mockOverview: ApiEnvelope<OverviewData> = {
  source: 'mock',
  data: {
    totalEquity: 1052340,
    balance: 996800,
    usedMargin: 42100,
    freeMargin: 1010240,
    unrealized: 43440,
    dailyPnl: 12034,
    grossExposure: 1.82,
    netExposure: 0.34,
    activeStrategies: 12,
    openAlerts: 2,
    runningJobs: 6,
    pnlSeries: [
      { name: 'Mon', value: 998000 },
      { name: 'Tue', value: 1007000 },
      { name: 'Wed', value: 1013000 },
      { name: 'Thu', value: 1034000 },
      { name: 'Fri', value: 1052340 },
    ],
  },
};

export const mockPortfolioOverview: ApiEnvelope<PortfolioOverview> = {
  source: 'mock',
  data: {
    totalEquity: 1052340,
    balance: 996800,
    usedMargin: 42100,
    freeMargin: 1010240,
    unrealized: 43440,
    grossExposure: 1.82,
    netExposure: 0.34,
    realizedPnl: 12034,
    unrealizedPnl: 4201,
    fillRate: 0.97,
    expectedVolatility: 0.18,
    expectedSharpe: 1.92,
    lastUpdated: new Date().toISOString(),
  },
};

export const mockPositions: ApiEnvelope<PositionRow[]> = {
  source: 'mock',
  data: [
    { symbol: 'BTCUSDT', side: 'long', quantity: 1.2, avgPrice: 43000, markPrice: 44120, pnl: 1340, strategyId: 'momentum', alphaFamily: 'momentum' },
    { symbol: 'ETHUSDT', side: 'short', quantity: 5, avgPrice: 3200, markPrice: 3150, pnl: 250, strategyId: 'meanrev', alphaFamily: 'mean_reversion' },
    { symbol: 'SOLUSDT', side: 'long', quantity: 80, avgPrice: 90, markPrice: 92, pnl: 160, strategyId: 'statarb', alphaFamily: 'statistical' },
  ],
};

export const mockRisk: ApiEnvelope<RiskSnapshot> = {
  source: 'mock',
  data: { grossExposure: 1.82, netExposure: 0.34, var1d: 0.018, drawdown: 0.032, concentration: 0.12, killSwitch: 'normal' },
};

export const mockMonitoring: ApiEnvelope<MonitoringSystem> = {
  source: 'mock',
  data: { cpu: 0.32, memory: 0.41, disk: 'OK', dbWritable: true, exchangeLatencyMs: 32, dataFreshnessSec: 8 },
};

export const mockAlerts: ApiEnvelope<AlertRow[]> = {
  source: 'mock',
  data: [
    { id: 'a1', severity: 'warning', status: 'open', message: 'Latency spike detected', createdAt: new Date().toISOString() },
    { id: 'a2', severity: 'critical', status: 'open', message: 'Risk threshold near breach', createdAt: new Date().toISOString() },
  ],
};

export const mockJobs: ApiEnvelope<JobRow[]> = {
  source: 'mock',
  data: [
    { name: 'system_health', nextRun: '30s', lastRun: 'ok', status: 'running', durationMs: 204 },
    { name: 'exchange_health', nextRun: '60s', lastRun: 'ok', status: 'running', durationMs: 355 },
    { name: 'portfolio_rebalance', nextRun: '15m', lastRun: 'ok', status: 'idle', durationMs: 1400 },
  ],
};

'use client';

import { KpiCard } from '@/components/cards/kpi-card';
import { DataStatusPill, resolveDataStatus } from '@/components/shared/data-status';
import { ErrorState } from '@/components/shared/error-state';
import { LoadingState } from '@/components/shared/loading-state';
import { SimpleTable } from '@/components/tables/simple-table';
import { usePortfolioMetrics, usePortfolioOverview, usePositions } from '@/lib/api/hooks';
import type { DataStatus, PortfolioMetrics, PortfolioOverview } from '@/types/api';

const EMPTY_PORTFOLIO: PortfolioOverview = {
  totalEquity: 0,
  balance: 0,
  usedMargin: 0,
  freeMargin: 0,
  unrealized: 0,
  grossExposure: 0,
  netExposure: 0,
  realizedPnl: 0,
  unrealizedPnl: 0,
  lastUpdated: '',
};

const EMPTY_METRICS: PortfolioMetrics = {
  fillRate: 0,
  expectedVolatility: 0,
  expectedSharpe: 0,
  lastUpdated: '',
};

function fmt(value: number) {
  return Number.isFinite(value) ? value.toFixed(4) : '-';
}

function labelize(value?: string) {
  if (!value) return '-';
  return value
    .split('_')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function mapBuildStatus(buildStatus?: string, hasData = false): DataStatus | undefined {
  switch (buildStatus) {
    case 'stale_cache':
      return 'stale';
    case 'degraded_live':
      return hasData ? 'fallback' : 'no_data';
    case 'live':
    case 'fresh_cache':
      return 'ok';
    default:
      return undefined;
  }
}

function fmtFreshness(buildStatus?: string, sourceSnapshotTime?: string, dataFreshnessSec?: number) {
  const parts: string[] = [];
  if (buildStatus) parts.push(labelize(buildStatus));
  if (dataFreshnessSec != null && Number.isFinite(dataFreshnessSec)) parts.push(`age ${Math.round(dataFreshnessSec)}s`);
  if (sourceSnapshotTime) parts.push(`snapshot ${sourceSnapshotTime}`);
  return parts.length ? parts.join(' | ') : '-';
}

export default function PortfolioPage() {
  const overview = usePortfolioOverview();
  const metrics = usePortfolioMetrics();
  const positions = usePositions();

  const overviewEnvelope = overview.data;
  const hasOverviewData = Boolean(overviewEnvelope && 'data' in overviewEnvelope && overviewEnvelope.data);
  if (overview.isLoading && !hasOverviewData) return <LoadingState />;
  if (overview.error && !hasOverviewData) return <ErrorState message="Portfolio overview load failed" />;

  const data = hasOverviewData ? overviewEnvelope!.data : EMPTY_PORTFOLIO;
  const metricsData = metrics.data?.data ?? EMPTY_METRICS;
  const positionsFeed = positions.data?.data;
  const rows = positionsFeed?.items ?? [];
  const overviewStatus = resolveDataStatus({
    status: mapBuildStatus(hasOverviewData ? data.buildStatus : undefined, hasOverviewData),
    isLoading: overview.isLoading,
    hasData: hasOverviewData,
    error: overview.error,
  });
  const metricsStatus = resolveDataStatus({
    status: mapBuildStatus(metrics.data?.data?.buildStatus, Boolean(metrics.data?.data)),
    isLoading: metrics.isLoading,
    hasData: Boolean(metrics.data?.data),
    error: metrics.error,
  });
  const positionsStatus = resolveDataStatus({
    status: mapBuildStatus(positionsFeed?.buildStatus, rows.length > 0),
    isLoading: positions.isLoading,
    hasData: rows.length > 0,
    error: positions.error,
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <h1 className="section-title">Portfolio</h1>
        <div className="flex flex-wrap items-center gap-2">
          <DataStatusPill label="Overview" status={overviewStatus} />
          <DataStatusPill label="Metrics" status={metricsStatus} />
          <DataStatusPill label="Positions" status={positionsStatus} />
        </div>
      </div>
      {overview.error ? <div className="rounded-md border border-amber-700/40 bg-amber-950/30 px-3 py-2 text-xs text-amber-200">Refresh failed. Showing last successful value.</div> : null}
      <div className="page-grid">
        <KpiCard title="Total Equity" value={data.totalEquity} />
        <KpiCard title="Balance" value={data.balance} />
        <KpiCard title="Used Margin" value={data.usedMargin} />
        <KpiCard title="Free Margin" value={data.freeMargin} />
        <KpiCard title="Unrealized" value={data.unrealized} />
        <KpiCard title="Gross Exposure" value={data.grossExposure} />
        <KpiCard title="Net Exposure" value={data.netExposure} />
        <KpiCard title="Expected Sharpe" value={metricsData.expectedSharpe} />
      </div>
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-sm text-slate-300">
        <div className="font-medium text-slate-100">Stable Summary</div>
        <div className="mt-2 grid gap-2 md:grid-cols-2">
          <div>Portfolio snapshot: <span className="text-slate-100">{fmtFreshness(data.buildStatus, data.sourceSnapshotTime, data.dataFreshnessSec)}</span></div>
          <div>Metrics snapshot: <span className="text-slate-100">{fmtFreshness(metricsData.buildStatus, metricsData.sourceSnapshotTime, metricsData.dataFreshnessSec)}</span></div>
          <div>Positions snapshot: <span className="text-slate-100">{fmtFreshness(positionsFeed?.buildStatus, positionsFeed?.sourceSnapshotTime, positionsFeed?.dataFreshnessSec)}</span></div>
        </div>
      </div>
      <div className="text-xs text-slate-400">Equity formula: Total Equity = Used Margin + Free Margin = Balance + Unrealized {data.lastUpdated ? `| as of ${data.lastUpdated}` : ''}</div>
      <SimpleTable
        headers={['Symbol', 'Side', 'Qty', 'Avg', 'Mark', 'PnL', 'Strategy', 'Alpha Family']}
        rows={rows.map((p) => [p.symbol, p.side, fmt(p.quantity), fmt(p.avgPrice), fmt(p.markPrice), fmt(p.pnl), p.strategyId || '-', p.alphaFamily || '-'])}
      />
    </div>
  );
}

'use client';

import { KpiCard } from '@/components/cards/kpi-card';
import { ErrorState } from '@/components/shared/error-state';
import { LoadingState } from '@/components/shared/loading-state';
import { SimpleTable } from '@/components/tables/simple-table';
import { usePortfolioOverview, usePositions } from '@/lib/api/hooks';
import type { PortfolioOverview } from '@/types/api';

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
  expectedVolatility: 0,
  expectedSharpe: 0,
  lastUpdated: '',
};

function fmt(value: number) {
  return Number.isFinite(value) ? value.toFixed(4) : '-';
}

export default function PortfolioPage() {
  const overview = usePortfolioOverview();
  const positions = usePositions();

  const overviewEnvelope = overview.data;
  const hasOverviewData = Boolean(overviewEnvelope && 'data' in overviewEnvelope && overviewEnvelope.data);
  if (overview.isLoading && !hasOverviewData) return <LoadingState />;
  if (overview.error && !hasOverviewData) return <ErrorState message="Portfolio overview load failed" />;

  const data = hasOverviewData ? overviewEnvelope!.data : EMPTY_PORTFOLIO;
  const rows = positions.data?.data ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <h1 className="section-title">Portfolio</h1>
        {overview.error ? <div className="rounded-md border border-amber-700/40 bg-amber-950/30 px-3 py-2 text-xs text-amber-200">Refresh failed. Showing last successful value.</div> : null}
      </div>
      <div className="page-grid">
        <KpiCard title="Total Equity" value={data.totalEquity} />
        <KpiCard title="Balance" value={data.balance} />
        <KpiCard title="Used Margin" value={data.usedMargin} />
        <KpiCard title="Free Margin" value={data.freeMargin} />
        <KpiCard title="Unrealized" value={data.unrealized} />
        <KpiCard title="Gross Exposure" value={data.grossExposure} />
        <KpiCard title="Net Exposure" value={data.netExposure} />
        <KpiCard title="Expected Sharpe" value={data.expectedSharpe} />
      </div>
      <div className="text-xs text-slate-400">Equity formula: Total Equity = Used Margin + Free Margin = Balance + Unrealized {data.lastUpdated ? `· as of ${data.lastUpdated}` : ''}</div>
      <SimpleTable
        headers={['Symbol', 'Side', 'Qty', 'Avg', 'Mark', 'PnL', 'Strategy', 'Alpha Family']}
        rows={rows.map((p) => [p.symbol, p.side, fmt(p.quantity), fmt(p.avgPrice), fmt(p.markPrice), fmt(p.pnl), p.strategyId || '-', p.alphaFamily || '-'])}
      />
    </div>
  );
}

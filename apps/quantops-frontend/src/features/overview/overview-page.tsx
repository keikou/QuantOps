'use client';

import { PnlLineChart } from '@/components/charts/pnl-line-chart';
import { KpiCard } from '@/components/cards/kpi-card';
import { ErrorState } from '@/components/shared/error-state';
import { LoadingState } from '@/components/shared/loading-state';
import { DataStatusBanner, DataStatusPill, resolveDataStatus } from '@/components/shared/data-status';
import { SimpleTable } from '@/components/tables/simple-table';
import { useAlerts, useEquityHistory, useMonitoringSystem, useOverview, useRiskSnapshot, useSchedulerJobs } from '@/lib/api/hooks';

function fmtMetric(value?: number) {
  if (value == null || Number.isNaN(value)) return '-';
  return value;
}

export function OverviewPage() {
  const overview = useOverview();
  const alerts = useAlerts();
  const jobs = useSchedulerJobs();
  const monitoring = useMonitoringSystem();
  const risk = useRiskSnapshot();
  const equityHistory = useEquityHistory();

  const overviewEnvelope = overview.data;
  const hasOverviewData = Boolean(overviewEnvelope && 'data' in overviewEnvelope && overviewEnvelope.data);
  if (overview.isLoading && !hasOverviewData) return <LoadingState />;
  if (overview.error && !hasOverviewData) return <ErrorState message="Overview load failed" />;

  const data = hasOverviewData ? overviewEnvelope!.data : undefined;
  const alertRows = alerts.data?.data ?? [];
  const openAlertRows = alertRows.filter((a) => a.status === 'open');
  const jobRows = jobs.data?.data ?? [];
  const monitoringData = monitoring.data?.data;
  const chartData = equityHistory.data?.data?.length ? equityHistory.data.data : (data?.pnlSeries ?? []);
  const displayedOpenAlerts = data?.openAlerts != null ? Math.max(data.openAlerts, openAlertRows.length) : (openAlertRows.length || '-');
  const executionReason = monitoringData?.executionReason || '-';
  const riskData = risk.data?.data;
  const overviewStatus = resolveDataStatus({ isLoading: overview.isLoading, hasData: Boolean(data), error: overview.error });
  const monitoringStatus = resolveDataStatus({ status: monitoringData?.dataStatus, isLoading: monitoring.isLoading, hasData: Boolean(monitoringData), error: monitoring.error });
  const riskStatus = resolveDataStatus({ status: riskData?.dataStatus, isLoading: risk.isLoading, hasData: Boolean(riskData), error: risk.error });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <h1 className="section-title">Overview</h1>
        <div className="flex flex-wrap items-center gap-2">
          <DataStatusPill label="Overview" status={overviewStatus} />
          <DataStatusPill label="Monitoring" status={monitoringStatus} />
          <DataStatusPill label="Risk" status={riskStatus} />
        </div>
      </div>
      {overview.error && data ? <DataStatusBanner label="Overview" status="fallback" reason="refresh_failed_fallback" asOf={data.asOf} /> : null}
      <DataStatusBanner label="Monitoring" status={monitoringStatus} reason={monitoringData?.statusReason} asOf={monitoringData?.asOf} />
      <DataStatusBanner label="Risk" status={riskStatus} reason={riskData?.statusReason} asOf={riskData?.asOf} />
      <div className="page-grid">
        <KpiCard title="Total Equity" value={fmtMetric(data?.totalEquity)} />
        <KpiCard title="Balance" value={fmtMetric(data?.balance)} />
        <KpiCard title="Used Margin" value={fmtMetric(data?.usedMargin)} />
        <KpiCard title="Free Margin" value={fmtMetric(data?.freeMargin)} />
        <KpiCard title="Unrealized" value={fmtMetric(data?.unrealized)} />
        <KpiCard title="Daily PnL" value={fmtMetric(data?.dailyPnl)} />
        <KpiCard title="Gross Exposure" value={fmtMetric(data?.grossExposure)} />
        <KpiCard title="Net Exposure" value={fmtMetric(data?.netExposure)} />
      </div>
      <div className="text-xs text-slate-400">Equity formula: Total Equity = Used Margin + Free Margin = Balance + Unrealized {data?.asOf ? `| as of ${data.asOf}` : ''}</div>
      <div className="grid gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2"><PnlLineChart data={chartData ?? []} /></div>
        <div className="card p-4">
          <div className="mb-4 text-sm text-slate-300">Live Snapshot</div>
          <div className="space-y-3 text-sm text-slate-300">
            <div>Active Strategies: {fmtMetric(data?.activeStrategies)}</div>
            <div>Open Alerts: {displayedOpenAlerts}</div>
            <div>Running Jobs: {fmtMetric(data?.runningJobs)}</div>
            <div>CPU: {monitoringData ? `${Math.round((monitoringData.cpu ?? 0) * 100)}%` : '-'}</div>
            <div>Exchange Latency: {monitoringData ? `${monitoringData.exchangeLatencyMs} ms` : '-'}</div>
            <div>Data Freshness: {monitoringData ? `${Math.round(monitoringData.dataFreshnessSec)} sec` : '-'}</div>
            <div>Execution State: {monitoringData?.executionState || '-'}</div>
            <div>Execution Reason: {executionReason}</div>
            <div>Worker Status: {monitoringData?.workerStatus || '-'}</div>
            <div>Monitoring Status: {monitoringStatus}</div>
            <div>Risk Status: {riskStatus}</div>
            <div>Risk Trading State: {riskData?.tradingState || monitoringData?.riskTradingState || '-'}</div>
            <div>Kill Switch: {riskData?.killSwitch || monitoringData?.killSwitch || '-'}</div>
          </div>
        </div>
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <SimpleTable
          headers={['Alert', 'Severity', 'Status']}
          rows={alertRows.map((a) => [a.message, a.severity, a.status])}
        />
        <SimpleTable
          headers={['Job', 'Status', 'Updated']}
          rows={jobRows.map((j) => [j.name, j.status, j.lastRun || j.nextRun || '-'])}
        />
      </div>
    </div>
  );
}

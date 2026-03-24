'use client';

import { useCallback, useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { PnlLineChart } from '@/components/charts/pnl-line-chart';
import { KpiCard } from '@/components/cards/kpi-card';
import { CommandCenterLive, type CommandCenterLiveEventType } from '@/components/realtime/command-center-live';
import { ErrorState } from '@/components/shared/error-state';
import { LoadingState } from '@/components/shared/loading-state';
import { DataStatusBanner, DataStatusPill, resolveDataStatus } from '@/components/shared/data-status';
import { RuntimeBlockCard, RuntimeStatusBadgeStrip, RuntimeSummaryCards, RuntimeTimelinePanel } from '@/components/shared/runtime-observability';
import { SimpleTable } from '@/components/tables/simple-table';
import { useAlerts, useCommandCenterRuntimeLatest, useEquityHistory, useMonitoringSystem, useOverview, usePortfolioMetrics, useRiskSnapshot, useSchedulerJobs } from '@/lib/api/hooks';
import type { ApiEnvelope, CommandCenterRealtimeEvent, OverviewData } from '@/types/api';

function fmtMetric(value?: number) {
  if (value == null || Number.isNaN(value)) return '-';
  return value;
}

const OVERVIEW_POLL_MS = 15000;
const OVERVIEW_REFRESH_THROTTLE_MS = 5000;
const OVERVIEW_LIVE_EVENT_TYPES: CommandCenterLiveEventType[] = ['pnl_update'];

function OverviewLiveUpdates() {
  const queryClient = useQueryClient();
  const lastRefreshAtRef = useRef(0);
  const refreshInFlightRef = useRef(false);
  const pendingRefreshRef = useRef(false);
  const refreshTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const requestRefreshRef = useRef<(() => Promise<void>) | null>(null);

  const clearRefreshTimer = useCallback(() => {
    if (!refreshTimerRef.current) return;
    clearTimeout(refreshTimerRef.current);
    refreshTimerRef.current = null;
  }, []);

  const scheduleRefresh = useCallback((delayMs: number) => {
    if (refreshTimerRef.current) return;
    refreshTimerRef.current = setTimeout(() => {
      refreshTimerRef.current = null;
      void requestRefreshRef.current?.();
    }, delayMs);
  }, []);

  const requestRefresh = useCallback(async () => {
    const now = Date.now();
    const elapsedMs = now - lastRefreshAtRef.current;

    if (refreshInFlightRef.current) {
      pendingRefreshRef.current = true;
      return;
    }

    if (elapsedMs < OVERVIEW_REFRESH_THROTTLE_MS) {
      pendingRefreshRef.current = true;
      scheduleRefresh(OVERVIEW_REFRESH_THROTTLE_MS - elapsedMs);
      return;
    }

    pendingRefreshRef.current = false;
    clearRefreshTimer();
    refreshInFlightRef.current = true;
    lastRefreshAtRef.current = now;

    try {
      await queryClient.refetchQueries({ queryKey: ['overview'], exact: true, type: 'active' });
    } finally {
      refreshInFlightRef.current = false;
      if (pendingRefreshRef.current) {
        const nextDelayMs = Math.max(OVERVIEW_REFRESH_THROTTLE_MS - (Date.now() - lastRefreshAtRef.current), 0);
        scheduleRefresh(nextDelayMs);
      }
    }
  }, [clearRefreshTimer, queryClient, scheduleRefresh]);

  requestRefreshRef.current = requestRefresh;

  const applyPnlUpdate = useCallback((event: CommandCenterRealtimeEvent) => {
    if (event.event_type !== 'pnl_update') return;

    queryClient.setQueryData<ApiEnvelope<OverviewData> | undefined>(['overview'], (current) => {
      if (!current?.data) return current;

      const payload = event.payload as Record<string, unknown>;
      return {
        ...current,
        data: {
          ...current.data,
          asOf: event.as_of || current.data.asOf,
          totalEquity: typeof payload.portfolio_value === 'number' ? payload.portfolio_value : current.data.totalEquity,
          dailyPnl: typeof payload.pnl === 'number' ? payload.pnl : current.data.dailyPnl,
          grossExposure: typeof payload.gross_exposure === 'number' ? payload.gross_exposure : current.data.grossExposure,
          netExposure: typeof payload.net_exposure === 'number' ? payload.net_exposure : current.data.netExposure,
          activeStrategies: typeof payload.active_strategies === 'number' ? payload.active_strategies : current.data.activeStrategies,
        },
      };
    });

    void requestRefresh();
  }, [queryClient, requestRefresh]);

  useEffect(() => {
    const interval = setInterval(() => {
      void requestRefresh();
    }, OVERVIEW_POLL_MS);

    return () => {
      clearInterval(interval);
      clearRefreshTimer();
    };
  }, [clearRefreshTimer, requestRefresh]);

  return <CommandCenterLive eventTypes={OVERVIEW_LIVE_EVENT_TYPES} onEvent={applyPnlUpdate} showBadge={false} />;
}

export function OverviewPage() {
  const overview = useOverview();
  const hasOverviewData = Boolean(overview.data && 'data' in overview.data && overview.data.data);
  const primaryReady = hasOverviewData || Boolean(overview.error);
  const runtime = useCommandCenterRuntimeLatest(primaryReady);
  const runtimeReady = primaryReady && Boolean(runtime.data?.data || runtime.error);
  const monitoring = useMonitoringSystem(runtimeReady);
  const monitoringReady = runtimeReady && Boolean(monitoring.data?.data || monitoring.error);
  const risk = useRiskSnapshot(monitoringReady);
  const riskReady = monitoringReady && Boolean(risk.data?.data || risk.error);
  const secondaryReady = riskReady && Boolean(
    runtime.data?.data || monitoring.data?.data || risk.data?.data || runtime.error || monitoring.error || risk.error
  );
  const portfolioMetricsQuery = usePortfolioMetrics(primaryReady);
  const alerts = useAlerts(secondaryReady);
  const jobs = useSchedulerJobs(secondaryReady);
  const equityHistory = useEquityHistory(secondaryReady);

  const overviewEnvelope = overview.data;
  if (overview.isLoading && !hasOverviewData) return <LoadingState />;
  if (overview.error && !hasOverviewData) return <ErrorState message="Overview load failed" />;

  const data = hasOverviewData ? overviewEnvelope!.data : undefined;
  const alertRows = alerts.data?.data ?? [];
  const openAlertRows = alertRows.filter((a) => a.status === 'open');
  const jobRows = jobs.data?.data ?? [];
  const monitoringData = monitoring.data?.data;
  const portfolioMetrics = portfolioMetricsQuery.data?.data;
  const chartData = equityHistory.data?.data?.length ? equityHistory.data.data : (data?.pnlSeries ?? []);
  const displayedOpenAlerts = data?.openAlerts != null ? Math.max(data.openAlerts, openAlertRows.length) : (openAlertRows.length || '-');
  const executionReason = monitoringData?.executionReason || '-';
  const riskData = risk.data?.data;
  const runtimeData = runtime.data?.data;
  const overviewStatus = resolveDataStatus({ isLoading: overview.isLoading, hasData: Boolean(data), error: overview.error });
  const monitoringStatus = resolveDataStatus({ status: monitoringData?.dataStatus, isLoading: monitoring.isLoading, hasData: Boolean(monitoringData), error: monitoring.error });
  const riskStatus = resolveDataStatus({ status: riskData?.dataStatus, isLoading: risk.isLoading, hasData: Boolean(riskData), error: risk.error });

  return (
    <div className="space-y-6">
      <OverviewLiveUpdates />
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
        <KpiCard title="Fill Rate" value={portfolioMetricsQuery.isLoading && !portfolioMetrics ? '-' : fmtMetric(portfolioMetrics?.fillRate)} />
        <KpiCard title="Expected Sharpe" value={portfolioMetricsQuery.isLoading && !portfolioMetrics ? '-' : fmtMetric(portfolioMetrics?.expectedSharpe)} />
      </div>
      <div className="text-xs text-slate-400">Equity formula: Total Equity = Used Margin + Free Margin = Balance + Unrealized {data?.asOf ? `| as of ${data.asOf}` : ''}</div>
      <div className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div className="text-sm font-medium text-slate-200">Runtime Status</div>
          <RuntimeStatusBadgeStrip runtime={runtimeData} />
        </div>
        <RuntimeSummaryCards runtime={runtimeData} />
      </div>
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
        <RuntimeBlockCard runtime={runtimeData} />
        <RuntimeTimelinePanel runtime={runtimeData} compact />
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

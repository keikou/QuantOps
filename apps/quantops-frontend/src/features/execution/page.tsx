'use client';

import { KpiCard } from '@/components/cards/kpi-card';
import { DataStatusBanner, DataStatusPill, resolveDataStatus } from '@/components/shared/data-status';
import { LoadingState } from '@/components/shared/loading-state';
import { RuntimeBlockCard, RuntimeStatusBadgeStrip, RuntimeSummaryCards, RuntimeTimelinePanel } from '@/components/shared/runtime-observability';
import { SimpleTable } from '@/components/tables/simple-table';
import { useCommandCenterRuntimeLatest, useExecutionLatest, useExecutionOrders, useExecutionPlannerLatest, useExecutionStateLatest, useExecutionSummary } from '@/lib/api/hooks';

function fmtSec(value?: number) {
  if (value == null || Number.isNaN(value)) return '-';
  return `${Math.round(value)}s`;
}

function fmtMetric(value?: number) {
  if (value == null || Number.isNaN(value)) return '-';
  return value;
}

export default function Page() {
  const summary = useExecutionSummary();
  const latest = useExecutionLatest();
  const orders = useExecutionOrders();
  const planner = useExecutionPlannerLatest();
  const state = useExecutionStateLatest();
  const runtime = useCommandCenterRuntimeLatest();

  if (summary.isLoading && !summary.data) return <LoadingState />;

  const data = summary.data?.data;
  const rows = latest.data?.data ?? [];
  const orderRows = orders.data?.data ?? [];
  const plannerData = planner.data?.data;
  const stateData = state.data?.data;
  const runtimeData = runtime.data?.data;
  const plannerItems = plannerData?.items ?? [];
  const plannerRows = plannerItems.length
    ? plannerItems.map((r) => [
        r.symbol,
        r.side || '-',
        r.algo || '-',
        r.route || '-',
        r.activityState || (r.active ? 'active' : 'planned_only'),
        fmtSec(r.planAgeSec),
        fmtSec(r.lastExecutionAgeSec),
        `${r.orderCount ?? 0}/${r.fillCount ?? 0}`,
        r.effectiveStatus || '-',
      ])
    : [['-', '-', '-', '-', '-', '-', '-', '-', 'no plans']];

  const topAlgo = Object.entries(plannerData?.algoMix || {}).sort((a, b) => Number(b[1]) - Number(a[1]))[0]?.[0] ?? '-';
  const topRoute = Object.entries(plannerData?.routeMix || {}).sort((a, b) => Number(b[1]) - Number(a[1]))[0]?.[0] ?? '-';
  const primaryReason = stateData?.blockReasons?.[0]?.message || stateData?.blockReasons?.[0]?.code || stateData?.reason || '-';
  const summaryStatus = resolveDataStatus({ isLoading: summary.isLoading, hasData: Boolean(data), error: summary.error });
  const plannerStatus = resolveDataStatus({ isLoading: planner.isLoading, hasData: Boolean(plannerData), error: planner.error });
  const stateStatus = resolveDataStatus({ isLoading: state.isLoading, hasData: Boolean(stateData), error: state.error });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <h1 className="section-title">Execution</h1>
        <div className="flex flex-wrap items-center gap-2">
          <DataStatusPill label="Summary" status={summaryStatus} />
          <DataStatusPill label="Planner" status={plannerStatus} />
          <DataStatusPill label="State" status={stateStatus} />
        </div>
      </div>
      <DataStatusBanner label="Execution Summary" status={summaryStatus} reason={summary.error instanceof Error ? summary.error.message : undefined} asOf={data?.asOf} />
      <div className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div className="text-sm font-medium text-slate-200">Runtime Truth</div>
          <RuntimeStatusBadgeStrip runtime={runtimeData} />
        </div>
        <RuntimeSummaryCards runtime={runtimeData} />
      </div>
      <div className="page-grid">
        <KpiCard title="Fill Rate" value={fmtMetric(data?.fillRate)} />
        <KpiCard title="Avg Slippage (bps)" value={fmtMetric(data?.avgSlippageBps)} />
        <KpiCard title="Latency P50 (ms)" value={fmtMetric(data?.latencyMsP50)} />
        <KpiCard title="Venue Score" value={fmtMetric(data?.venueScore)} />
        <KpiCard title="Execution State" value={stateData?.executionState || '-'} />
        <KpiCard title="Reason" value={stateData?.reason || '-'} />
      </div>
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-sm text-slate-300">
        <div className="font-medium text-slate-100">Execution observability</div>
        <div className="mt-2 grid gap-2 md:grid-cols-2">
          <div>Trading state: <span className="text-slate-100">{stateData?.tradingState || plannerData?.tradingState || '-'}</span></div>
          <div>Primary reason: <span className="text-slate-100">{primaryReason}</span></div>
          <div>Planner age: <span className="text-slate-100">{fmtSec(stateData?.plannerAgeSec)}</span></div>
          <div>Last execution age: <span className="text-slate-100">{fmtSec(stateData?.executionAgeSec)}</span></div>
          <div>Last fill age: <span className="text-slate-100">{fmtSec(stateData?.lastFillAgeSec)}</span></div>
          <div>Submitted / Open orders: <span className="text-slate-100">{stateData?.submittedOrderCount ?? '-'} / {stateData?.openOrderCount ?? '-'}</span></div>
        </div>
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <RuntimeBlockCard runtime={runtimeData} />
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-sm text-slate-300">
          <div className="font-medium text-slate-100">Bridge Counters</div>
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            <div>Operator state: <span className="text-slate-100">{runtimeData?.operatorState || '-'}</span></div>
            <div>Planner status: <span className="text-slate-100">{runtimeData?.plannerStatus || '-'}</span></div>
            <div>Planned count: <span className="text-slate-100">{runtimeData?.plannedCount ?? '-'}</span></div>
            <div>Submitted count: <span className="text-slate-100">{runtimeData?.submittedCount ?? '-'}</span></div>
            <div>Blocked count: <span className="text-slate-100">{runtimeData?.blockedCount ?? '-'}</span></div>
            <div>Filled count: <span className="text-slate-100">{runtimeData?.filledCount ?? '-'}</span></div>
            <div>Latest transition: <span className="text-slate-100">{runtimeData?.lastTransitionAt || '-'}</span></div>
          </div>
        </div>
      </div>
      <RuntimeTimelinePanel runtime={runtimeData} />
      <SimpleTable
        headers={['Symbol', 'Side', 'Qty', 'Fill Price', 'Slippage', 'Latency', 'Status']}
        rows={rows.length ? rows.map((r) => [r.symbol, r.side || '-', r.fillQty ?? '-', r.fillPrice ?? '-', r.slippageBps ?? '-', r.latencyMs ?? '-', r.status || '-']) : [['-', '-', '-', '-', '-', '-', 'no fills']]}
      />

      <SimpleTable
        headers={['Order ID', 'Plan ID', 'Symbol', 'Side', 'Qty', 'Venue', 'Algo', 'Status']}
        rows={orderRows.length ? orderRows.map((r) => [r.orderId || '-', r.planId || '-', r.symbol, r.side || '-', r.qty ?? '-', r.venue || '-', r.algo || '-', r.status || '-']) : [['-', '-', '-', '-', '-', '-', '-', 'no orders']]}
      />

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-100">Execution Planner</h2>
          <div className="text-xs text-slate-400">Latest plan as of {plannerData?.asOf || '-'} | Latest activity {plannerData?.latestActivityAt || '-'}</div>
        </div>
        <div className="page-grid">
          <KpiCard title="Trading State" value={plannerData?.tradingState || stateData?.tradingState || '-'} />
          <KpiCard title="Active Plans" value={fmtMetric(plannerData?.planCount)} />
          <KpiCard title="Visible Plans" value={fmtMetric(plannerData?.visiblePlanCount)} />
          <KpiCard title="Expired Plans" value={fmtMetric(plannerData?.expiredCount)} />
          <KpiCard title="Top Algo / Route" value={`${topAlgo} / ${topRoute}`} />
          <KpiCard title="Open Orders" value={fmtMetric(stateData?.openOrderCount)} />
        </div>
        <SimpleTable
          headers={['Symbol', 'Side', 'Algo', 'Route', 'Activity', 'Plan Age', 'Last Exec Age', 'Orders/Fills', 'Status']}
          rows={plannerRows}
        />
      </div>
    </div>
  );
}

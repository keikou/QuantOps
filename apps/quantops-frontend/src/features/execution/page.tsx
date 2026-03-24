'use client';

import Link from 'next/link';
import { useCallback, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

import { KpiCard } from '@/components/cards/kpi-card';
import { CommandCenterLive } from '@/components/realtime/command-center-live';
import { DataStatusBanner, DataStatusPill, resolveDataStatus } from '@/components/shared/data-status';
import { LoadingState } from '@/components/shared/loading-state';
import { RuntimeBlockCard, RuntimeStatusBadgeStrip, RuntimeSummaryCards, RuntimeTimelinePanel } from '@/components/shared/runtime-observability';
import { SimpleTable } from '@/components/tables/simple-table';
import { normalizeCommandCenterRuntimeRuns, normalizeRuntimeIssueBuckets } from '@/lib/api/normalize';
import { useCommandCenterRuntimeIssues, useCommandCenterRuntimeLatest, useCommandCenterRuntimeRuns, useExecutionLatest, useExecutionOrders, useExecutionPlannerLatest, useExecutionStateLatest, useExecutionSummary } from '@/lib/api/hooks';
import type { ApiEnvelope, CommandCenterRealtimeEvent, CommandCenterRuntimeRunSummary, RuntimeIssueBucket } from '@/types/api';

type RuntimeFilterKey =
  | 'all'
  | 'blocked'
  | 'degraded'
  | 'submitted_no_fill'
  | 'failed'
  | 'filled'
  | 'missing_price'
  | 'risk_guard_block'
  | 'incomplete_chain'
  | 'no_artifact';

function fmtSec(value?: number) {
  if (value == null || Number.isNaN(value)) return '-';
  return `${Math.round(value)}s`;
}

function fmtMetric(value?: number) {
  if (value == null || Number.isNaN(value)) return '-';
  return value;
}

function labelize(value?: string) {
  if (!value) return '-';
  return value
    .split('_')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

const diagnosisViews: Array<{ label: string; issueCode?: string; retryability?: string; reasonCode?: string }> = [
  { label: 'Missing Price', issueCode: 'missing_price' },
  { label: 'Risk Guard', issueCode: 'risk_guard_block' },
  { label: 'Execution Bridge', issueCode: 'execution_bridge_missing' },
  { label: 'Fill Capture Gap', issueCode: 'fill_not_captured' },
  { label: 'Incomplete Chain', reasonCode: 'NO_POSITION_DELTA' },
  { label: 'Persistent Issues' },
  { label: 'Retryable Issues', retryability: 'retryable' },
];

const RUNTIME_WINDOW_MINUTES = 5;
const RUNTIME_ISSUE_LIMIT = 5;
const EXECUTION_ROW_LIMIT = 10;

function runtimeRunsQueryKey(filters?: {
  limit?: number;
  windowMinutes?: number;
  operatorState?: string;
  bridgeState?: string;
  issueCode?: string;
  reasonCode?: string;
  blockingComponent?: string;
  degraded?: boolean;
  eventChainComplete?: boolean;
  artifactAvailable?: boolean;
}) {
  return ['command-center-runtime-runs', filters?.limit ?? 25, filters?.windowMinutes ?? 5, filters?.operatorState ?? '', filters?.bridgeState ?? '', filters?.issueCode ?? '', filters?.reasonCode ?? '', filters?.blockingComponent ?? '', filters?.degraded ?? 'any', filters?.eventChainComplete ?? 'any', filters?.artifactAvailable ?? 'any'] as const;
}

function runtimeIssuesQueryKey(limit = 25, windowMinutes = RUNTIME_WINDOW_MINUTES) {
  return ['command-center-runtime-issues', limit, windowMinutes] as const;
}

function matchesRuntimeFilters(
  row: CommandCenterRuntimeRunSummary,
  filters: {
    operatorState?: string;
    bridgeState?: string;
    issueCode?: string;
    reasonCode?: string;
    blockingComponent?: string;
    degraded?: boolean;
    eventChainComplete?: boolean;
    artifactAvailable?: boolean;
  },
) {
  if (filters.operatorState && row.operatorState !== filters.operatorState) return false;
  if (filters.bridgeState && row.bridgeState !== filters.bridgeState) return false;
  if (filters.issueCode && (row.diagnosisCode || row.diagnosis?.primaryCode) !== filters.issueCode) return false;
  if (filters.reasonCode && row.latestReasonCode !== filters.reasonCode) return false;
  if (filters.blockingComponent && row.blockingComponent !== filters.blockingComponent) return false;
  if (filters.degraded != null && row.degraded !== filters.degraded) return false;
  if (filters.eventChainComplete != null && row.eventChainComplete !== filters.eventChainComplete) return false;
  if (filters.artifactAvailable != null && row.artifactAvailable !== filters.artifactAvailable) return false;
  return true;
}

function upsertRuntimeRun(rows: CommandCenterRuntimeRunSummary[], incoming: CommandCenterRuntimeRunSummary, limit: number) {
  return [incoming, ...rows.filter((row) => row.runId !== incoming.runId)].slice(0, limit);
}

function ExecutionLiveUpdates({
  runFilters,
  issueLimit,
}: {
  runFilters: {
    limit?: number;
    windowMinutes?: number;
    operatorState?: string;
    bridgeState?: string;
    issueCode?: string;
    reasonCode?: string;
    blockingComponent?: string;
    degraded?: boolean;
    eventChainComplete?: boolean;
    artifactAvailable?: boolean;
  };
  issueLimit: number;
}) {
  const queryClient = useQueryClient();
  const onEvent = useCallback((event: CommandCenterRealtimeEvent) => {
    if (event.event_type === 'runtime_run') {
      const incoming = normalizeCommandCenterRuntimeRuns({ items: [event.payload] })[0];
      if (!incoming?.runId) return;
      queryClient.setQueryData<ApiEnvelope<CommandCenterRuntimeRunSummary[]>>(runtimeRunsQueryKey(runFilters), (previous) => {
        const current = previous?.data ?? [];
        const filtered = matchesRuntimeFilters(incoming, runFilters)
          ? upsertRuntimeRun(current, incoming, runFilters.limit ?? 25)
          : current.filter((row) => row.runId !== incoming.runId);
        return { data: filtered, source: 'live' };
      });
      return;
    }

    if (event.event_type === 'runtime_issue') {
      const payloadItems = Array.isArray((event.payload as { items?: unknown[] }).items) ? ((event.payload as { items?: unknown[] }).items ?? []) : [];
      const issueItems = normalizeRuntimeIssueBuckets({ items: payloadItems }).slice(0, issueLimit);
      queryClient.setQueryData<ApiEnvelope<RuntimeIssueBucket[]>>(runtimeIssuesQueryKey(issueLimit, RUNTIME_WINDOW_MINUTES), {
        data: issueItems,
        source: 'live',
      });
    }
  }, [issueLimit, queryClient, runFilters]);

  return <CommandCenterLive eventTypes={['runtime_run', 'runtime_issue']} onEvent={onEvent} showBadge={false} />;
}

export default function Page() {
  const [runtimeFilter, setRuntimeFilter] = useState<RuntimeFilterKey>('all');
  const [issueCodeFilter, setIssueCodeFilter] = useState('');
  const [reasonFilter, setReasonFilter] = useState('');
  const [componentFilter, setComponentFilter] = useState('');
  const summary = useExecutionSummary();
  const summaryReady = Boolean(summary.data?.data) || Boolean(summary.error);
  const runtime = useCommandCenterRuntimeLatest(summaryReady);
  const runtimeReady = summaryReady && Boolean(runtime.data?.data || runtime.error);
  const planner = useExecutionPlannerLatest(runtimeReady);
  const plannerReady = runtimeReady && Boolean(planner.data?.data || planner.error);
  const state = useExecutionStateLatest(plannerReady);
  const stateReady = plannerReady && Boolean(state.data?.data || state.error);
  const detailReady = stateReady && Boolean(
    runtime.data?.data || planner.data?.data || state.data?.data || runtime.error || planner.error || state.error
  );
  const latest = useExecutionLatest(detailReady, EXECUTION_ROW_LIMIT);
  const orders = useExecutionOrders(detailReady, EXECUTION_ROW_LIMIT);
  const runtimeIssues = useCommandCenterRuntimeIssues(RUNTIME_ISSUE_LIMIT, detailReady, RUNTIME_WINDOW_MINUTES);
  const runtimeViewFilters: {
    operatorState?: string;
    reasonCode?: string;
    issueCode?: string;
    blockingComponent?: string;
    degraded?: boolean;
    eventChainComplete?: boolean;
    artifactAvailable?: boolean;
  } =
    runtimeFilter === 'all'
      ? {}
      : runtimeFilter === 'degraded'
        ? { degraded: true as const }
        : runtimeFilter === 'incomplete_chain'
          ? { eventChainComplete: false as const }
          : runtimeFilter === 'no_artifact'
            ? { artifactAvailable: false as const }
            : runtimeFilter === 'missing_price'
              ? { reasonCode: 'MISSING_PRICE' }
              : runtimeFilter === 'risk_guard_block'
                ? { reasonCode: 'RISK_GUARD_BLOCK' }
                : { operatorState: runtimeFilter };
  const runtimeRuns = useCommandCenterRuntimeRuns(
    {
      limit: 25,
      windowMinutes: RUNTIME_WINDOW_MINUTES,
      ...runtimeViewFilters,
      issueCode: issueCodeFilter || runtimeViewFilters.issueCode,
      reasonCode: reasonFilter || runtimeViewFilters.reasonCode,
      blockingComponent: componentFilter || runtimeViewFilters.blockingComponent,
    },
    detailReady
  );

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
  const runtimeRunsData = runtimeRuns.data?.data ?? [];
  const runtimeIssueRows = runtimeIssues.data?.data ?? [];
  const runtimeFilterOptions: Array<{ key: RuntimeFilterKey; label: string }> = [
    { key: 'all', label: 'All' },
    { key: 'blocked', label: 'Blocked' },
    { key: 'degraded', label: 'Degraded' },
    { key: 'submitted_no_fill', label: 'Submitted-No-Fill' },
    { key: 'failed', label: 'Failed' },
    { key: 'filled', label: 'Filled' },
    { key: 'missing_price', label: 'Missing Price' },
    { key: 'risk_guard_block', label: 'Risk Guard' },
    { key: 'incomplete_chain', label: 'Incomplete Chain' },
    { key: 'no_artifact', label: 'No Artifact' },
  ];

  return (
    <div className="space-y-6">
      <ExecutionLiveUpdates
        runFilters={{
          limit: 25,
          windowMinutes: RUNTIME_WINDOW_MINUTES,
          ...runtimeViewFilters,
          issueCode: issueCodeFilter || runtimeViewFilters.issueCode,
          reasonCode: reasonFilter || runtimeViewFilters.reasonCode,
          blockingComponent: componentFilter || runtimeViewFilters.blockingComponent,
        }}
        issueLimit={RUNTIME_ISSUE_LIMIT}
      />
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

      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="font-medium text-slate-100">Active Runtime Issues</div>
            <div className="text-sm text-slate-400">Diagnosis rollups highlight repeating runtime patterns and the next operator check.</div>
          </div>
          {issueCodeFilter || reasonFilter || componentFilter ? (
            <button
              type="button"
              onClick={() => {
                setIssueCodeFilter('');
                setReasonFilter('');
                setComponentFilter('');
              }}
              className="rounded-full border border-slate-700 bg-slate-800/70 px-3 py-1 text-xs text-slate-200 transition hover:border-slate-600 hover:text-slate-100"
            >
              Clear Diagnosis Filters
            </button>
          ) : null}
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {issueCodeFilter ? (
            <span className="rounded-full border border-cyan-500/40 bg-cyan-500/10 px-3 py-1 text-xs text-cyan-100">
              Diagnosis: {labelize(issueCodeFilter)}
            </span>
          ) : null}
          {reasonFilter ? (
            <span className="rounded-full border border-cyan-500/40 bg-cyan-500/10 px-3 py-1 text-xs text-cyan-100">
              Reason: {labelize(reasonFilter)}
            </span>
          ) : null}
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {diagnosisViews.map((view) => (
            <button
              key={view.label}
              type="button"
              onClick={() => {
                setIssueCodeFilter(view.issueCode || '');
                setReasonFilter(view.reasonCode || '');
              }}
              className={`rounded-full border px-3 py-1 text-xs transition ${
                (view.issueCode && issueCodeFilter === view.issueCode) || (view.reasonCode && reasonFilter === view.reasonCode)
                  ? 'border-cyan-500/40 bg-cyan-500/10 text-cyan-100'
                  : 'border-slate-700 bg-slate-800/70 text-slate-300 hover:border-slate-600 hover:text-slate-100'
              }`}
            >
              {view.label}
            </button>
          ))}
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {runtimeIssueRows.length ? runtimeIssueRows.slice(0, 4).map((issue) => (
            <button
              key={issue.code}
              type="button"
              onClick={() => setIssueCodeFilter(issue.code)}
              className={`rounded-2xl border p-4 text-left transition ${
                issueCodeFilter === issue.code
                  ? 'border-cyan-500/40 bg-cyan-500/10'
                  : 'border-slate-800 bg-slate-950/60 hover:border-cyan-500/30'
              }`}
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-medium text-slate-100">{labelize(issue.code)}</div>
                  <div className="rounded-full border border-slate-700 bg-slate-800/70 px-2 py-0.5 text-[11px] text-slate-200">{issue.count}</div>
                </div>
              <div className="mt-2 text-xs text-slate-400">{issue.severity} | {issue.retryability} | {issue.recurrenceStatus} | {issue.trend}</div>
              <div className="mt-2 text-sm text-slate-300">{issue.operatorAction}</div>
              <div className="mt-3 text-xs text-cyan-200">Component: {issue.likelyComponent || '-'}</div>
              <div className="mt-1 text-xs text-slate-500">Seen in {issue.distinctRunCount} of last {issue.windowRunCount} runs</div>
              <div className="mt-1 text-xs text-slate-500">Example run: {issue.exampleRunId || '-'}</div>
            </button>
          )) : (
            <div className="text-sm text-slate-400">No active runtime issues detected.</div>
          )}
        </div>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="font-medium text-slate-100">Recent Runtime Runs</div>
            <div className="text-sm text-slate-400">Historical triage across the latest runs, using the same semantics as run detail.</div>
          </div>
          <div className="flex flex-wrap gap-2">
            {runtimeFilterOptions.map((option) => (
              <button
                key={option.key}
                type="button"
                onClick={() => setRuntimeFilter(option.key)}
                className={`rounded-full border px-3 py-1 text-xs transition ${
                  runtimeFilter === option.key
                    ? 'border-cyan-500/40 bg-cyan-500/10 text-cyan-100'
                    : 'border-slate-700 bg-slate-800/70 text-slate-300 hover:border-slate-600 hover:text-slate-100'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <label className="text-sm text-slate-300">
            <div className="mb-1 text-xs uppercase tracking-wide text-slate-500">Reason Code</div>
            <input
              value={reasonFilter}
              onChange={(event) => setReasonFilter(event.target.value.toUpperCase())}
              placeholder="MISSING_PRICE"
              className="w-full rounded-xl border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 outline-none transition focus:border-cyan-500/40"
            />
          </label>
          <label className="text-sm text-slate-300">
            <div className="mb-1 text-xs uppercase tracking-wide text-slate-500">Blocking Component</div>
            <input
              value={componentFilter}
              onChange={(event) => setComponentFilter(event.target.value)}
              placeholder="execution_planner"
              className="w-full rounded-xl border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 outline-none transition focus:border-cyan-500/40"
            />
          </label>
        </div>
        <div className="mt-4 overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="border-b border-slate-800 text-slate-400">
              <tr>
                <th className="px-3 py-2 text-left font-medium">Run</th>
                <th className="px-3 py-2 text-left font-medium">Start</th>
                <th className="px-3 py-2 text-left font-medium">Operator</th>
                <th className="px-3 py-2 text-left font-medium">Bridge</th>
                <th className="px-3 py-2 text-left font-medium">Reason</th>
                <th className="px-3 py-2 text-left font-medium">Plans / Orders / Fills</th>
                <th className="px-3 py-2 text-left font-medium">Diagnosis</th>
                <th className="px-3 py-2 text-left font-medium">Flags</th>
                <th className="px-3 py-2 text-left font-medium">Detail</th>
              </tr>
            </thead>
            <tbody>
              {runtimeRunsData.length ? (
                runtimeRunsData.map((row) => (
                  <tr key={row.runId} className="border-b border-slate-800/80 text-slate-200">
                    <td className="px-3 py-3 align-top">
                      <div className="font-medium text-slate-100">{row.runId}</div>
                      <div className="text-xs text-slate-400">{row.completedAt || '-'}</div>
                    </td>
                    <td className="px-3 py-3 align-top text-slate-300">{row.startedAt || '-'}</td>
                    <td className="px-3 py-3 align-top">{labelize(row.operatorState)}</td>
                    <td className="px-3 py-3 align-top">{labelize(row.bridgeState)}</td>
                    <td className="px-3 py-3 align-top">
                      <div>{row.latestReasonSummary || labelize(row.latestReasonCode)}</div>
                      <div className="text-xs text-slate-400">{row.blockingComponent || '-'}</div>
                    </td>
                    <td className="px-3 py-3 align-top">{row.plannedCount} / {row.submittedCount} / {row.filledCount}</td>
                    <td className="px-3 py-3 align-top">
                      <div>{labelize(row.diagnosisCode || row.diagnosis?.primaryCode)}</div>
                      <div className="text-xs text-slate-400">{row.diagnosis?.retryability || '-'}</div>
                    </td>
                    <td className="px-3 py-3 align-top">
                      <div>{row.degraded ? 'Degraded' : 'Normal'}</div>
                      <div className="text-xs text-slate-400">
                        Chain {row.eventChainComplete ? 'complete' : 'incomplete'}{row.artifactAvailable ? ' · bundle' : ''}
                      </div>
                    </td>
                    <td className="px-3 py-3 align-top">
                      {row.detailPath ? (
                        <Link href={row.detailPath} className="text-cyan-200 transition hover:text-cyan-100">
                          Open
                        </Link>
                      ) : (
                        <span className="text-slate-500">-</span>
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr className="text-slate-400">
                  <td className="px-3 py-4" colSpan={9}>
                    {runtimeRuns.isLoading ? 'Loading recent runtime runs…' : 'No runs matched the current filter.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

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

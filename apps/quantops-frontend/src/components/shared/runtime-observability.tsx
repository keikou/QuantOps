'use client';

import Link from 'next/link';

import type { CommandCenterRuntimeDebug, CommandCenterRuntimeLatest } from '@/types/api';

function formatLabel(value: string): string {
  return value
    .split('_')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function formatTimestamp(value?: string): string {
  return value || '-';
}

function runtimeDetailPath(runtime?: CommandCenterRuntimeLatest): string {
  return runtime?.detailPath || (runtime?.runId ? `/execution/runs/${runtime.runId}` : '');
}

function badgeTone(severity: string): string {
  switch (severity) {
    case 'critical':
      return 'border-rose-500/40 bg-rose-500/10 text-rose-200';
    case 'high':
      return 'border-amber-500/40 bg-amber-500/10 text-amber-200';
    case 'medium':
      return 'border-sky-500/40 bg-sky-500/10 text-sky-200';
    default:
      return 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200';
  }
}

function operatorStateTone(state?: string): string {
  switch (state) {
    case 'filled':
      return 'border-emerald-500/40 bg-emerald-500/10 text-emerald-200';
    case 'submitted_no_fill':
      return 'border-amber-500/40 bg-amber-500/10 text-amber-200';
    case 'failed':
      return 'border-rose-500/40 bg-rose-500/10 text-rose-200';
    case 'blocked':
    case 'no_decision':
    case 'planned_blocked':
    case 'planned_not_submitted':
      return 'border-orange-500/40 bg-orange-500/10 text-orange-200';
    case 'degraded':
      return 'border-sky-500/40 bg-sky-500/10 text-sky-200';
    default:
      return 'border-cyan-500/30 bg-cyan-500/10 text-cyan-100';
  }
}

function stageTone(state?: string): string {
  switch (state) {
    case 'completed':
      return 'border-emerald-500/40 bg-emerald-500/10 text-emerald-200';
    case 'blocked':
      return 'border-orange-500/40 bg-orange-500/10 text-orange-200';
    case 'failed':
      return 'border-rose-500/40 bg-rose-500/10 text-rose-200';
    case 'degraded':
    case 'missing':
      return 'border-amber-500/40 bg-amber-500/10 text-amber-100';
    case 'not_applicable':
      return 'border-slate-700 bg-slate-800/70 text-slate-300';
    default:
      return 'border-cyan-500/30 bg-cyan-500/10 text-cyan-100';
  }
}

function RuntimeDetailLink({ runtime, label = 'Open Run Detail', subtle = false }: { runtime?: CommandCenterRuntimeLatest; label?: string; subtle?: boolean }) {
  const detailPath = runtimeDetailPath(runtime);
  if (!detailPath) return null;
  return (
    <Link
      href={detailPath}
      prefetch={false}
      className={
        subtle
          ? 'text-xs text-cyan-200 transition hover:text-cyan-100'
          : 'rounded-full border border-slate-700 bg-slate-800/70 px-3 py-1 text-xs text-cyan-100 transition hover:border-cyan-500/40 hover:text-cyan-50'
      }
    >
      {label}
    </Link>
  );
}

export function RuntimeStatusBadgeStrip({ runtime }: { runtime?: CommandCenterRuntimeLatest }) {
  const stateLabel = formatLabel(runtime?.operatorState || runtime?.bridgeState || 'no_decision');
  return (
    <div className="flex flex-wrap gap-2">
      <span className={`rounded-full border px-3 py-1 text-xs ${operatorStateTone(runtime?.operatorState)}`}>
        {stateLabel}
      </span>
      <span className="rounded-full border border-slate-700 bg-slate-800/70 px-3 py-1 text-xs text-slate-200">
        Bridge: {formatLabel(runtime?.bridgeState || 'no_decision')}
      </span>
      {runtime?.latestReasonCode ? (
        <span className="rounded-full border border-slate-700 bg-slate-800/70 px-3 py-1 text-xs text-slate-200">
          Reason: {formatLabel(runtime.latestReasonCode)}
        </span>
      ) : null}
      {runtime?.degraded ? (
        <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs text-amber-100">
          Degraded
        </span>
      ) : null}
      <RuntimeDetailLink runtime={runtime} label="Investigate Run" />
    </div>
  );
}

export function RuntimeSummaryCards({ runtime }: { runtime?: CommandCenterRuntimeLatest }) {
  const cards = [
    { title: 'Current Bridge State', value: formatLabel(runtime?.bridgeState || 'no_decision') },
    { title: 'Latest Reason', value: runtime?.latestReasonSummary || formatLabel(runtime?.latestReasonCode || '') || '-' },
    { title: 'Last Fill', value: formatTimestamp(runtime?.lastSuccessfulFillAt) },
    { title: 'Last Portfolio Update', value: formatTimestamp(runtime?.lastSuccessfulPortfolioUpdateAt) },
    { title: 'Last Completed Cycle', value: formatTimestamp(runtime?.lastCycleCompletedAt) },
    { title: 'Degraded State', value: runtime?.degraded ? 'yes' : 'no' },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {cards.map((card) => (
        <div key={card.title} className="card p-4">
          <div className="text-sm text-slate-400">{card.title}</div>
          <div className="mt-2 text-base font-semibold text-slate-100">{card.value}</div>
          <div className="mt-3">
            <RuntimeDetailLink runtime={runtime} label="View detail" subtle />
          </div>
        </div>
      ))}
    </div>
  );
}

export function RuntimeBlockCard({ runtime }: { runtime?: CommandCenterRuntimeLatest }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-sm text-slate-300">
      <div className="flex items-center justify-between gap-3">
        <div className="font-medium text-slate-100">Runtime Observability</div>
        <div className="flex items-center gap-2">
          <div className={`rounded-full border px-3 py-1 text-xs ${operatorStateTone(runtime?.operatorState)}`}>
            {formatLabel(runtime?.operatorState || runtime?.bridgeState || 'no_decision')}
          </div>
          <RuntimeDetailLink runtime={runtime} />
        </div>
      </div>
      <div className="mt-3 space-y-2">
        <div>Operator message: <span className="text-slate-100">{runtime?.operatorMessage || '-'}</span></div>
        <div>Latest reason: <span className="text-slate-100">{runtime?.latestReasonSummary || runtime?.latestReasonCode || '-'}</span></div>
        <div>Blocking component: <span className="text-slate-100">{runtime?.blockingComponent || '-'}</span></div>
        <div>Run / Cycle: <span className="text-slate-100">{runtime?.runId || '-'} / {runtime?.cycleId || '-'}</span></div>
        <div>Last successful fill: <span className="text-slate-100">{formatTimestamp(runtime?.lastSuccessfulFillAt)}</span></div>
        <div>Last portfolio update: <span className="text-slate-100">{formatTimestamp(runtime?.lastSuccessfulPortfolioUpdateAt)}</span></div>
        <div>Event chain complete: <span className="text-slate-100">{runtime?.eventChainComplete ? 'yes' : 'no'}</span></div>
        <div>Debug path: <span className="break-all text-cyan-200">{runtime?.debugPath || '-'}</span></div>
      </div>
      {runtime?.degradedFlags?.length ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {runtime.degradedFlags.map((flag) => (
            <span key={flag} className="rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs text-amber-100">
              {flag}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}

export function RuntimeTimelinePanel({ runtime, compact = false }: { runtime?: CommandCenterRuntimeLatest; compact?: boolean }) {
  const items = runtime?.timeline ?? [];
  if (!items.length) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-sm text-slate-400">
        Runtime timeline is not available yet.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="font-medium text-slate-100">Runtime Timeline</div>
        <div className="flex items-center gap-3">
          <RuntimeDetailLink runtime={runtime} label="View run detail" subtle />
          <div className="text-xs text-slate-400">{runtime?.lastTransitionAt || runtime?.generatedAt || '-'}</div>
        </div>
      </div>
      <div className={`grid gap-3 ${compact ? 'md:grid-cols-2' : ''}`}>
        {items.slice(0, compact ? 4 : 8).map((item, idx) => (
          <div key={`${item.eventType}-${item.timestamp}-${idx}`} className="rounded-xl border border-slate-800 bg-slate-950/60 p-3 text-sm">
            <div className="flex items-center justify-between gap-3">
              <div className="font-medium text-slate-100">{item.eventType}</div>
              <div className={`rounded-full border px-2 py-0.5 text-[11px] ${badgeTone(item.severity)}`}>{item.severity}</div>
            </div>
            <div className="mt-2 text-slate-300">{item.summary || '-'}</div>
            <div className="mt-2 grid gap-1 text-xs text-slate-400">
              <div>Status: {item.status}</div>
              <div>Reason: {item.reasonCode || '-'}</div>
              <div>Symbol: {item.symbol || '-'}</div>
              <div>At: {item.timestamp || '-'}</div>
              <div className="pt-1">
                <RuntimeDetailLink runtime={runtime} label="Inspect this run" subtle />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function RuntimeStageTimelinePanel({ debug }: { debug?: CommandCenterRuntimeDebug }) {
  const stages = debug?.stages ?? [];
  if (!stages.length) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-sm text-slate-400">
        Structured stage timeline is not available yet.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="font-medium text-slate-100">Run Stage Timeline</div>
        <div className="text-xs text-slate-400">
          {debug?.run?.status || '-'} | {debug?.run?.durationMs ?? 0}ms
        </div>
      </div>
      <div className="space-y-3">
        {stages.map((stage) => (
          <div key={stage.key} className="rounded-xl border border-slate-800 bg-slate-950/60 p-3 text-sm">
            <div className="flex items-center justify-between gap-3">
              <div className="font-medium text-slate-100">{stage.title}</div>
              <div className={`rounded-full border px-2 py-0.5 text-[11px] ${stageTone(stage.state)}`}>
                {formatLabel(stage.state)}
              </div>
            </div>
            <div className="mt-2 text-slate-300">{stage.summary || '-'}</div>
            <div className="mt-2 grid gap-1 text-xs text-slate-400">
              <div>At: {stage.timestamp || '-'}</div>
              <div>Reason: {stage.reasonCode || '-'}</div>
            </div>
            {stage.evidence?.length ? (
              <div className="mt-3 flex flex-wrap gap-2">
                {stage.evidence.map((item) => (
                  <span key={`${stage.key}-${item}`} className="rounded-full border border-slate-700 bg-slate-900/70 px-2 py-1 text-[11px] text-slate-300">
                    {item}
                  </span>
                ))}
              </div>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}

'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';

import { KpiCard } from '@/components/cards/kpi-card';
import { ErrorState } from '@/components/shared/error-state';
import { LoadingState } from '@/components/shared/loading-state';
import { RuntimeBlockCard, RuntimeStageTimelinePanel, RuntimeStatusBadgeStrip, RuntimeSummaryCards, RuntimeTimelinePanel } from '@/components/shared/runtime-observability';
import { useCommandCenterRuntimeDebug } from '@/lib/api/hooks';
import type { CommandCenterRuntimeLatest } from '@/types/api';

function DebugPayloadCard({ title, payload }: { title: string; payload: unknown }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
      <div className="mb-3 font-medium text-slate-100">{title}</div>
      <pre className="overflow-x-auto rounded-xl bg-slate-950/70 p-3 text-xs text-slate-300">
        {JSON.stringify(payload ?? {}, null, 2)}
      </pre>
    </div>
  );
}

export default function Page() {
  const params = useParams<{ runId: string }>();
  const runId = typeof params?.runId === 'string' ? params.runId : '';
  const runtime = useCommandCenterRuntimeDebug(runId);

  if (runtime.isLoading && !runtime.data) return <LoadingState />;
  if (runtime.error && !runtime.data) return <ErrorState message="Runtime run detail failed" />;

  const detail = runtime.data?.data;
  const summary = detail?.summary;
  const runtimeCardData: CommandCenterRuntimeLatest | undefined = detail
    ? {
        status: detail.status,
        runId: summary?.runId,
        cycleId: summary?.cycleId,
        bridgeState: summary?.bridgeState || 'no_decision',
        operatorState: summary?.operatorState || summary?.bridgeState || 'no_decision',
        plannerStatus: summary?.plannerStatus || 'unknown',
        plannedCount: summary?.plannedCount ?? 0,
        submittedCount: summary?.submittedCount ?? 0,
        blockedCount: summary?.blockedCount ?? 0,
        filledCount: summary?.filledCount ?? 0,
        eventChainComplete: Boolean(summary?.eventChainComplete),
        latestReasonCode: summary?.latestReasonCode,
        latestReasonSummary: summary?.latestReasonSummary,
        blockingComponent: summary?.blockingComponent,
        degraded: Boolean(summary?.degraded),
        degradedFlags: summary?.degradedFlags ?? [],
        operatorMessage: summary?.operatorMessage,
        generatedAt: '',
        lastTransitionAt: detail.asOf,
        lastSuccessfulFillAt: summary?.lastSuccessfulFillAt,
        lastSuccessfulPortfolioUpdateAt: summary?.lastSuccessfulPortfolioUpdateAt,
        lastCycleCompletedAt: summary?.lastCycleCompletedAt,
        debugPath: `/api/v1/command-center/debug/runtime?run_id=${encodeURIComponent(runId)}`,
        detailPath: `/execution/runs/${encodeURIComponent(runId)}`,
        timeline: detail.timeline ?? [],
      }
    : undefined;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-sm text-slate-400">Run Detail</div>
          <h1 className="section-title">{runId || 'Unknown run'}</h1>
        </div>
        <Link href="/execution" className="rounded-full border border-slate-700 bg-slate-800/70 px-4 py-2 text-sm text-slate-100 transition hover:border-cyan-500/40 hover:text-cyan-100">
          Back to Execution
        </Link>
      </div>

      <RuntimeStatusBadgeStrip runtime={runtimeCardData} />
      <RuntimeSummaryCards runtime={runtimeCardData} />

      <div className="page-grid">
        <KpiCard title="Planner Rows" value={Number(detail?.counts?.planner_rows ?? 0)} />
        <KpiCard title="Event Rows" value={Number(detail?.counts?.event_rows ?? 0)} />
        <KpiCard title="Reason Rows" value={Number(detail?.counts?.reason_rows ?? 0)} />
        <KpiCard title="Duration (ms)" value={Number(detail?.run?.durationMs ?? 0)} />
        <KpiCard title="Snapshot Age (sec)" value={Number(detail?.timings?.snapshotAgeSec ?? 0)} />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-sm text-slate-300">
          <div className="font-medium text-slate-100">Run Forensics</div>
          <div className="mt-2 grid gap-2 md:grid-cols-2">
            <div>Status: <span className="text-slate-100">{detail?.run?.status || '-'}</span></div>
            <div>Triggered by: <span className="text-slate-100">{detail?.run?.triggeredBy || '-'}</span></div>
            <div>Mode: <span className="text-slate-100">{detail?.run?.mode || '-'}</span></div>
            <div>Job: <span className="text-slate-100">{detail?.run?.jobName || '-'}</span></div>
            <div>Started at: <span className="text-slate-100">{detail?.run?.startedAt || '-'}</span></div>
            <div>Finished at: <span className="text-slate-100">{detail?.run?.finishedAt || '-'}</span></div>
          </div>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-sm text-slate-300">
          <div className="font-medium text-slate-100">Diagnostic Bundle</div>
          <div className="mt-2">Artifact: <span className="text-slate-100">{detail?.artifacts?.bundle?.name || detail?.provenance?.artifactBundle?.name || '-'}</span></div>
          <div className="mt-1 break-all text-xs text-cyan-200">{detail?.artifacts?.bundle?.path || detail?.provenance?.artifactBundle?.path || 'No local artifact bundle found for this run.'}</div>
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            <div>Checkpoints: <span className="text-slate-100">{detail?.artifacts?.checkpointCount ?? 0}</span></div>
            <div>Audit logs: <span className="text-slate-100">{detail?.artifacts?.auditLogCount ?? 0}</span></div>
            <div>Available: <span className="text-slate-100">{detail?.artifacts?.available?.join(', ') || '-'}</span></div>
            <div>Missing: <span className="text-slate-100">{detail?.artifacts?.missing?.join(', ') || '-'}</span></div>
          </div>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <RuntimeBlockCard runtime={runtimeCardData} />
        <RuntimeTimelinePanel runtime={runtimeCardData} />
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-sm text-slate-300">
        <div className="font-medium text-slate-100">Diagnosis</div>
        <div className="mt-3 grid gap-2 md:grid-cols-2">
          <div>Primary: <span className="text-slate-100">{detail?.diagnosis?.primaryCode || '-'}</span></div>
          <div>Severity: <span className="text-slate-100">{detail?.diagnosis?.severity || '-'}</span></div>
          <div>Retryability: <span className="text-slate-100">{detail?.diagnosis?.retryability || '-'}</span></div>
          <div>Likely component: <span className="text-slate-100">{detail?.diagnosis?.likelyComponent || '-'}</span></div>
          <div>Recent recurrence: <span className="text-slate-100">{detail?.diagnosisContext?.seenInRecentRuns || '-'}</span></div>
          <div>Trend / status: <span className="text-slate-100">{detail?.diagnosisContext?.trend || '-'} / {detail?.diagnosisContext?.recurrenceStatus || '-'}</span></div>
        </div>
        <div className="mt-3">Recommended check: <span className="text-slate-100">{detail?.diagnosis?.operatorAction || '-'}</span></div>
        <div className="mt-1">Confidence: <span className="text-slate-100">{detail?.diagnosis?.confidence ?? 0}</span></div>
      </div>

      <RuntimeStageTimelinePanel debug={detail} />

      <div className="grid gap-4 xl:grid-cols-2">
        <DebugPayloadCard title="Run Record" payload={detail?.raw?.run} />
        <DebugPayloadCard title="Planner Truth" payload={detail?.raw?.planner} />
        <DebugPayloadCard title="Bridge Diagnostics" payload={detail?.raw?.bridge} />
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <DebugPayloadCard title="Runtime Events" payload={detail?.raw?.events} />
        <DebugPayloadCard title="Runtime Reasons" payload={detail?.raw?.reasons} />
      </div>
    </div>
  );
}

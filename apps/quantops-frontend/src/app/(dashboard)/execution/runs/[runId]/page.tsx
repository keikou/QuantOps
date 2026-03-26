'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useState } from 'react';

import { KpiCard } from '@/components/cards/kpi-card';
import { ErrorState } from '@/components/shared/error-state';
import { LoadingState } from '@/components/shared/loading-state';
import { RuntimeBlockCard, RuntimeStageTimelinePanel, RuntimeStatusBadgeStrip, RuntimeSummaryCards, RuntimeTimelinePanel } from '@/components/shared/runtime-observability';
import { useCommandCenterRuntimeDebug, useReviewRuntimeRun } from '@/lib/api/hooks';
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
  const reviewRuntimeRun = useReviewRuntimeRun();
  const [operatorNote, setOperatorNote] = useState('');
  const [reviewError, setReviewError] = useState('');

  if (runtime.isLoading && !runtime.data) return <LoadingState />;
  if (runtime.error && !runtime.data) return <ErrorState message="Runtime run detail failed" />;

  const detail = runtime.data?.data;
  const linkedEvidence = detail?.linkedEvidence;
  const retryGuidance = detail?.retryGuidance;
  const review = detail?.review;
  const summary = detail?.summary;
  const allowedTransitions = review?.allowedTransitions ?? ['acknowledged', 'investigating', 'resolved', 'ignored'];

  function submitReview(status: string, acknowledged: boolean, note: string) {
    if (status === 'resolved' && !note.trim()) {
      setReviewError('A note is required before marking a run as resolved.');
      return;
    }
    setReviewError('');
    reviewRuntimeRun.mutate({ runId, reviewStatus: status, operatorNote: note, acknowledged });
  }
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
          {(detail?.artifacts?.bundle?.path || detail?.provenance?.artifactBundle?.path) ? (
            <button
              type="button"
              onClick={async () => {
                await navigator.clipboard.writeText(detail?.artifacts?.bundle?.path || detail?.provenance?.artifactBundle?.path || '');
              }}
              className="mt-3 rounded-full border border-slate-700 bg-slate-800/70 px-3 py-1 text-xs text-slate-100 transition hover:border-cyan-500/40 hover:text-cyan-100"
            >
              Copy Bundle Path
            </button>
          ) : null}
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            <div>Checkpoints: <span className="text-slate-100">{detail?.artifacts?.checkpointCount ?? 0}</span></div>
            <div>Audit logs: <span className="text-slate-100">{detail?.artifacts?.auditLogCount ?? 0}</span></div>
            <div>Available: <span className="text-slate-100">{detail?.artifacts?.available?.join(', ') || '-'}</span></div>
            <div>Missing: <span className="text-slate-100">{detail?.artifacts?.missing?.join(', ') || '-'}</span></div>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-sm text-slate-300">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="font-medium text-slate-100">Operator Review</div>
            <div className="text-xs text-slate-500">Read/write-light workflow state for runtime triage.</div>
          </div>
          <div className="rounded-full border border-slate-700 bg-slate-800/70 px-3 py-1 text-xs text-slate-200">
            {review?.reviewStatus || 'new'}
          </div>
        </div>
        <div className="mt-3 grid gap-2 md:grid-cols-2">
          <div>Acknowledged: <span className="text-slate-100">{review?.acknowledged ? 'Yes' : 'No'}</span></div>
          <div>Reviewed by: <span className="text-slate-100">{review?.reviewedBy || '-'}</span></div>
          <div>Reviewed at: <span className="text-slate-100">{review?.reviewedAt || '-'}</span></div>
          <div>Current note: <span className="text-slate-100">{review?.operatorNote || '-'}</span></div>
        </div>
        <textarea
          value={operatorNote}
          onChange={(event) => {
            setOperatorNote(event.target.value);
            if (reviewError) setReviewError('');
          }}
          placeholder="Add operator note"
          className="mt-4 min-h-24 w-full rounded-2xl border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 outline-none transition focus:border-cyan-500/40"
        />
        {reviewError ? (
          <div className="mt-2 text-xs text-amber-300">{reviewError}</div>
        ) : null}
        <div className="mt-3 flex flex-wrap gap-2">
          {['acknowledged', 'investigating', 'resolved', 'ignored'].map((status) => (
            <button
              key={status}
              type="button"
              disabled={reviewRuntimeRun.isPending || !runId || !allowedTransitions.includes(status)}
              onClick={() => submitReview(status, true, operatorNote)}
              className="rounded-full border border-slate-700 bg-slate-800/70 px-3 py-1 text-xs text-slate-100 transition hover:border-cyan-500/40 hover:text-cyan-100 disabled:cursor-not-allowed disabled:opacity-60"
            >
              Mark {status}
            </button>
          ))}
          <button
            type="button"
            disabled={reviewRuntimeRun.isPending || !runId || ((review?.reviewStatus || 'new') !== 'new' && !allowedTransitions.includes('new'))}
            onClick={() => submitReview('new', false, '')}
            className="rounded-full border border-slate-700 bg-slate-800/70 px-3 py-1 text-xs text-slate-100 transition hover:border-slate-600 hover:text-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Reset Review
          </button>
        </div>
        <div className="mt-3 text-[11px] text-slate-500">
          Allowed next states: {allowedTransitions.length ? allowedTransitions.join(', ') : 'none'}
        </div>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-sm text-slate-300">
        <div className="font-medium text-slate-100">Linked Evidence</div>
        <div className="mt-2 text-xs text-slate-500">Jump to related runtime slices without reconstructing filters manually.</div>
        <div className="mt-4 flex flex-wrap gap-2">
          {linkedEvidence?.executionIssuePath ? (
            <a href={linkedEvidence.executionIssuePath} className="rounded-full border border-slate-700 bg-slate-800/70 px-3 py-1 text-xs text-slate-100 transition hover:border-cyan-500/40 hover:text-cyan-100">
              Related Diagnosis Runs
            </a>
          ) : null}
          {linkedEvidence?.executionComponentPath ? (
            <a href={linkedEvidence.executionComponentPath} className="rounded-full border border-slate-700 bg-slate-800/70 px-3 py-1 text-xs text-slate-100 transition hover:border-cyan-500/40 hover:text-cyan-100">
              Same Component
            </a>
          ) : null}
          {linkedEvidence?.executionReasonPath ? (
            <a href={linkedEvidence.executionReasonPath} className="rounded-full border border-slate-700 bg-slate-800/70 px-3 py-1 text-xs text-slate-100 transition hover:border-cyan-500/40 hover:text-cyan-100">
              Same Reason Code
            </a>
          ) : null}
          {linkedEvidence?.runtimeRunsApiPath ? (
            <a href={linkedEvidence.runtimeRunsApiPath} target="_blank" rel="noreferrer" className="rounded-full border border-slate-700 bg-slate-800/70 px-3 py-1 text-xs text-slate-100 transition hover:border-cyan-500/40 hover:text-cyan-100">
              Filtered Runs API
            </a>
          ) : null}
          {linkedEvidence?.runtimeIssueApiPath ? (
            <a href={linkedEvidence.runtimeIssueApiPath} target="_blank" rel="noreferrer" className="rounded-full border border-slate-700 bg-slate-800/70 px-3 py-1 text-xs text-slate-100 transition hover:border-cyan-500/40 hover:text-cyan-100">
              Issue Bucket API
            </a>
          ) : null}
        </div>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-sm text-slate-300">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="font-medium text-slate-100">Retry Guidance</div>
            <div className="text-xs text-slate-500">Non-destructive operator guidance only. No retry execution is triggered here.</div>
          </div>
          <div className={`rounded-full border px-3 py-1 text-xs ${
            retryGuidance?.retryCandidate
              ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-100'
              : 'border-amber-500/40 bg-amber-500/10 text-amber-100'
          }`}>
            {retryGuidance?.retryCandidate ? 'Retry Candidate' : 'Retry Blocked'}
          </div>
        </div>
        <div className="mt-3 grid gap-2 md:grid-cols-2">
          <div>Retry scope: <span className="text-slate-100">{retryGuidance?.retryScope || '-'}</span></div>
          <div>Retry reason: <span className="text-slate-100">{retryGuidance?.retryReason || '-'}</span></div>
          <div className="md:col-span-2">Suggested action: <span className="text-slate-100">{retryGuidance?.suggestedAction || '-'}</span></div>
          <div className="md:col-span-2">Block reason: <span className="text-slate-100">{retryGuidance?.retryBlockReason || '-'}</span></div>
        </div>
        {retryGuidance?.copyableCommand ? (
          <>
            <pre className="mt-4 overflow-x-auto rounded-xl bg-slate-950/70 p-3 text-xs text-cyan-200">
              {retryGuidance.copyableCommand}
            </pre>
            <button
              type="button"
              onClick={async () => {
                await navigator.clipboard.writeText(retryGuidance.copyableCommand || '');
              }}
              className="mt-3 rounded-full border border-slate-700 bg-slate-800/70 px-3 py-1 text-xs text-slate-100 transition hover:border-cyan-500/40 hover:text-cyan-100"
            >
              Copy Retry Command
            </button>
          </>
        ) : null}
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

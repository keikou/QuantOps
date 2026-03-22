'use client'

import { useMemo, useState } from 'react'
import { useCurrentUser, usePauseSchedulerJob, useResumeSchedulerJob, useRunSchedulerJob, useSchedulerJobs } from '@/lib/api/hooks'
import { LoadingState } from '@/components/shared/loading-state'
import { ErrorState } from '@/components/shared/error-state'
import { ActionButton } from '@/components/shared/action-button'
import { MutationStatus } from '@/components/shared/mutation-status'
import { ConfirmModal } from '@/components/shared/confirm-modal'
import { PermissionGate } from '@/components/shared/permission-gate'
import { useUiStore } from '@/store/ui-store'
import { getArray, getRole } from '@/lib/api/normalize'

type JobRow = {
  id?: string
  name?: string
  nextRun?: string
  lastRun?: string
  status?: string
  durationMs?: number
}

type PendingAction = { type: 'run' | 'pause' | 'resume'; job: string } | null

export default function SchedulerPage() {
  const jobsQuery = useSchedulerJobs()
  const userQuery = useCurrentUser()
  const role = useUiStore((s) => s.roleOverride) ?? getRole(userQuery?.data)
  const runJob = useRunSchedulerJob()
  const pauseJob = usePauseSchedulerJob()
  const resumeJob = useResumeSchedulerJob()
  const [message, setMessage] = useState<string | null>(null)
  const [pendingAction, setPendingAction] = useState<PendingAction>(null)
  const pending = runJob.isPending || pauseJob.isPending || resumeJob.isPending
  const modalDescription = useMemo(() => {
    if (!pendingAction) return ''
    return `Job ${pendingAction.job} に対して ${pendingAction.type} を実行します。監査ログへ記録されます。`
  }, [pendingAction])

  const jobs = getArray<JobRow>(jobsQuery?.data)

  if (jobsQuery?.isLoading) return <LoadingState />
  if (jobsQuery?.isError) return <ErrorState message="Failed to load scheduler jobs." />

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Scheduler</h1>
      <MutationStatus message={message} error={[runJob, pauseJob, resumeJob].map((m) => (m.error instanceof Error ? m.error.message : null)).find(Boolean) || null} />
      <div className="overflow-hidden rounded-2xl border border-white/10 bg-slate-900/60">
        <table className="min-w-full text-sm">
          <thead className="bg-white/5 text-left text-slate-300">
            <tr>
              <th className="px-4 py-3">Job</th>
              <th className="px-4 py-3">Next Run</th>
              <th className="px-4 py-3">Last Run</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Duration</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {jobs.length === 0 ? (
              <tr>
                <td className="px-4 py-3 text-slate-400" colSpan={6}>No jobs</td>
              </tr>
            ) : (
              jobs.map((job, idx) => {
                const jobName = job.name ?? job.id ?? `job-${idx}`
                return (
                  <tr key={jobName} className="border-t border-white/5">
                    <td className="px-4 py-3">{jobName}</td>
                    <td className="px-4 py-3">{job.nextRun ?? '-'}</td>
                    <td className="px-4 py-3">{job.lastRun ?? '-'}</td>
                    <td className="px-4 py-3 capitalize">{job.status ?? '-'}</td>
                    <td className="px-4 py-3">{typeof job.durationMs === 'number' ? `${job.durationMs} ms` : '-'}</td>
                    <td className="px-4 py-3">
                      <PermissionGate role={role} permission="scheduler.control">
                        <div className="flex gap-2">
                          <ActionButton label="Run" disabled={pending} onClick={() => setPendingAction({ type: 'run', job: jobName })} />
                          <ActionButton label="Pause" tone="secondary" disabled={pending} onClick={() => setPendingAction({ type: 'pause', job: jobName })} />
                          <ActionButton label="Resume" tone="secondary" disabled={pending} onClick={() => setPendingAction({ type: 'resume', job: jobName })} />
                        </div>
                      </PermissionGate>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>

      <ConfirmModal
        open={!!pendingAction}
        title="Scheduler action"
        description={modalDescription}
        pending={pending}
        onClose={() => setPendingAction(null)}
        onConfirm={async () => {
          if (!pendingAction) return
          const map = {
            run: runJob.mutateAsync,
            pause: pauseJob.mutateAsync,
            resume: resumeJob.mutateAsync,
          } as const
          const result = await map[pendingAction.type](pendingAction.job)
          setMessage(result.data.message)
          setPendingAction(null)
        }}
      />
    </div>
  )
}

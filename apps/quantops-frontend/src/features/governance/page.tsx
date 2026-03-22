'use client'

import { useMemo, useState } from 'react'
import { useApproveGovernance, useCurrentUser, useGovernanceApprovals, useRejectGovernance } from '@/lib/api/hooks'
import { LoadingState } from '@/components/shared/loading-state'
import { ErrorState } from '@/components/shared/error-state'
import { ActionButton } from '@/components/shared/action-button'
import { MutationStatus } from '@/components/shared/mutation-status'
import { ConfirmModal } from '@/components/shared/confirm-modal'
import { PermissionGate } from '@/components/shared/permission-gate'
import { useUiStore } from '@/store/ui-store'
import { getArray, getRole } from '@/lib/api/normalize'

type ReviewAction = { type: 'approve' | 'reject'; id: string; alphaId: string } | null

type ApprovalRow = {
  id?: string
  alphaId?: string
  target?: string
  status?: string
  sharpe?: number
  updatedAt?: string
}

export default function GovernancePage() {
  const approvalsQuery = useGovernanceApprovals()
  const userQuery = useCurrentUser()
  const role = useUiStore((s) => s.roleOverride) ?? getRole(userQuery?.data)
  const approve = useApproveGovernance()
  const reject = useRejectGovernance()
  const [message, setMessage] = useState<string | null>(null)
  const [reviewAction, setReviewAction] = useState<ReviewAction>(null)
  const pending = approve.isPending || reject.isPending
  const description = useMemo(() => {
    if (!reviewAction) return ''
    return `${reviewAction.alphaId} を ${reviewAction.type === 'approve' ? '承認' : '却下'}します。監査ログへ記録されます。`
  }, [reviewAction])

  const approvals = getArray<ApprovalRow>(approvalsQuery?.data)

  if (approvalsQuery?.isLoading) return <LoadingState />
  if (approvalsQuery?.isError) return <ErrorState message="Failed to load governance approvals." />

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Governance</h1>
      <MutationStatus message={message} error={[approve, reject].map((m) => (m.error instanceof Error ? m.error.message : null)).find(Boolean) || null} />
      <div className="overflow-hidden rounded-2xl border border-white/10 bg-slate-900/60">
        <table className="min-w-full text-sm">
          <thead className="bg-white/5 text-left text-slate-300">
            <tr>
              <th className="px-4 py-3">Alpha</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Sharpe</th>
              <th className="px-4 py-3">Updated</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {approvals.length === 0 ? (
              <tr>
                <td className="px-4 py-3 text-slate-400" colSpan={5}>No approval items</td>
              </tr>
            ) : (
              approvals.map((row, idx) => {
                const id = row.id ?? `${row.alphaId ?? row.target ?? 'approval'}-${idx}`
                const alphaId = row.alphaId ?? row.target ?? id
                const status = row.status ?? 'pending'
                return (
                  <tr key={id} className="border-t border-white/5">
                    <td className="px-4 py-3">{alphaId}</td>
                    <td className="px-4 py-3 capitalize">{status}</td>
                    <td className="px-4 py-3">{row.sharpe ?? '-'}</td>
                    <td className="px-4 py-3">{row.updatedAt ? new Date(row.updatedAt).toLocaleString() : '-'}</td>
                    <td className="px-4 py-3">
                      <PermissionGate role={role} permission="governance.review">
                        <div className="flex gap-2">
                          <ActionButton label="Approve" disabled={pending || status !== 'pending'} onClick={() => setReviewAction({ type: 'approve', id, alphaId })} />
                          <ActionButton label="Reject" tone="danger" disabled={pending || status !== 'pending'} onClick={() => setReviewAction({ type: 'reject', id, alphaId })} />
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
        open={!!reviewAction}
        title="Governance decision"
        description={description}
        tone={reviewAction?.type === 'reject' ? 'danger' : 'default'}
        confirmLabel={reviewAction?.type === 'reject' ? 'Reject' : 'Approve'}
        pending={pending}
        onClose={() => setReviewAction(null)}
        onConfirm={async () => {
          if (!reviewAction) return
          const result = reviewAction.type === 'approve'
            ? await approve.mutateAsync(reviewAction.id)
            : await reject.mutateAsync(reviewAction.id)
          setMessage(result.data.message)
          setReviewAction(null)
        }}
      />
    </div>
  )
}

'use client'

import { useMemo, useState } from 'react'
import { useAcknowledgeAlert, useAlerts, useCurrentUser } from '@/lib/api/hooks'
import { LoadingState } from '@/components/shared/loading-state'
import { ErrorState } from '@/components/shared/error-state'
import { ActionButton } from '@/components/shared/action-button'
import { MutationStatus } from '@/components/shared/mutation-status'
import { ConfirmModal } from '@/components/shared/confirm-modal'
import { PermissionGate } from '@/components/shared/permission-gate'
import { useUiStore } from '@/store/ui-store'
import { getArray, getRole } from '@/lib/api/normalize'

type AlertRow = {
  id?: string
  severity?: 'info' | 'warning' | 'critical'
  status?: 'open' | 'closed'
  message?: string
  createdAt?: string
  source?: string
}

export default function AlertsPage() {
  const alertsQuery = useAlerts()
  const userQuery = useCurrentUser()
  const role = useUiStore((s) => s.roleOverride) ?? getRole(userQuery?.data)
  const ack = useAcknowledgeAlert()
  const [message, setMessage] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const alerts = getArray<AlertRow>(alertsQuery?.data)

  const selected = useMemo(
    () => alerts.find((alert) => alert.id === selectedId) ?? null,
    [alerts, selectedId]
  )

  if (alertsQuery?.isLoading) return <LoadingState />
  if (alertsQuery?.isError) return <ErrorState message="Failed to load alerts." />

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Alerts</h1>
          <p className="text-sm text-slate-400">確認モーダルと監査ログ付きの運用アクション。</p>
        </div>
      </div>
      <MutationStatus message={message} error={ack.error instanceof Error ? ack.error.message : null} />
      <div className="overflow-hidden rounded-2xl border border-white/10 bg-slate-900/60">
        <table className="min-w-full text-sm">
          <thead className="bg-white/5 text-left text-slate-300">
            <tr>
              <th className="px-4 py-3">Severity</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Message</th>
              <th className="px-4 py-3">Created</th>
              <th className="px-4 py-3">Action</th>
            </tr>
          </thead>
          <tbody>
            {alerts.length === 0 ? (
              <tr>
                <td className="px-4 py-3 text-slate-400" colSpan={5}>No alerts</td>
              </tr>
            ) : (
              alerts.map((alert, idx) => (
                <tr key={alert.id ?? `alert-${idx}`} className="border-t border-white/5">
                  <td className="px-4 py-3 capitalize">{alert.severity ?? '-'}</td>
                  <td className="px-4 py-3 capitalize">{alert.status ?? '-'}</td>
                  <td className="px-4 py-3">{alert.message ?? '-'}</td>
                  <td className="px-4 py-3">{alert.createdAt ? new Date(alert.createdAt).toLocaleString() : '-'}</td>
                  <td className="px-4 py-3">
                    <PermissionGate role={role} permission="alerts.ack">
                      <ActionButton
                        label="Acknowledge"
                        disabled={alert.status === 'closed' || ack.isPending || !alert.id}
                        onClick={() => setSelectedId(alert.id ?? null)}
                      />
                    </PermissionGate>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <ConfirmModal
        open={!!selected}
        title="Acknowledge alert"
        description={selected ? `Alert 「${selected.message ?? 'unknown'}」を確認済みにします。監査ログへ記録されます。` : ''}
        confirmLabel="Acknowledge"
        pending={ack.isPending}
        onClose={() => setSelectedId(null)}
        onConfirm={async () => {
          if (!selected?.id) return
          const result = await ack.mutateAsync(selected.id)
          setMessage(result.data.message)
          setSelectedId(null)
        }}
      />
    </div>
  )
}

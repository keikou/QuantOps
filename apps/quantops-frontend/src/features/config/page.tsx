'use client'

import { useEffect, useMemo, useState } from 'react'
import { useConfigCurrent, useCurrentUser, useSaveConfigDraft } from '@/lib/api/hooks'
import { LoadingState } from '@/components/shared/loading-state'
import { ErrorState } from '@/components/shared/error-state'
import { ActionButton } from '@/components/shared/action-button'
import { MutationStatus } from '@/components/shared/mutation-status'
import { ConfirmModal } from '@/components/shared/confirm-modal'
import { PermissionGate } from '@/components/shared/permission-gate'
import { useUiStore } from '@/store/ui-store'
import { getPayload, getRole } from '@/lib/api/normalize'

type ConfigShape = {
  schedulerCadenceSec: number
  riskLimit: number
  monitoringThreshold: number
  executionMode: 'paper' | 'shadow' | 'live'
  version?: string
}

const EMPTY_CONFIG: ConfigShape = {
  schedulerCadenceSec: 60,
  riskLimit: 0.1,
  monitoringThreshold: 0.9,
  executionMode: 'paper',
  version: 'local-default',
}

export default function ConfigPage() {
  const configQuery = useConfigCurrent()
  const userQuery = useCurrentUser()
  const role = useUiStore((s) => s.roleOverride) ?? getRole(userQuery?.data)
  const saveDraft = useSaveConfigDraft()
  const [message, setMessage] = useState<string | null>(null)
  const initial = useMemo<ConfigShape>(() => {
    return getPayload<ConfigShape>(configQuery?.data, EMPTY_CONFIG)
  }, [configQuery?.data])
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [form, setForm] = useState<ConfigShape>(EMPTY_CONFIG)

  useEffect(() => {
    setForm({
      schedulerCadenceSec: initial.schedulerCadenceSec ?? 60,
      riskLimit: initial.riskLimit ?? 0.1,
      monitoringThreshold: initial.monitoringThreshold ?? 0.9,
      executionMode: initial.executionMode ?? 'paper',
      version: initial.version ?? 'local-default',
    })
  }, [initial])

  if (configQuery?.isLoading) return <LoadingState />
  if (configQuery?.isError) return <ErrorState message="Failed to load config." />

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Config</h1>
      <p className="text-sm text-slate-400">Current draft version: {initial.version ?? 'local-default'}</p>
      <MutationStatus message={message} error={saveDraft.error instanceof Error ? saveDraft.error.message : null} />
      <div className="grid gap-4 rounded-2xl border border-white/10 bg-slate-900/60 p-6 md:grid-cols-2">
        <label className="space-y-2 text-sm">
          <span className="text-slate-300">Scheduler cadence (sec)</span>
          <input className="w-full rounded-lg border border-white/10 bg-slate-950 px-3 py-2" type="number" value={form.schedulerCadenceSec} onChange={(e) => setForm((prev) => ({ ...prev, schedulerCadenceSec: Number(e.target.value) }))} />
        </label>
        <label className="space-y-2 text-sm">
          <span className="text-slate-300">Risk limit</span>
          <input className="w-full rounded-lg border border-white/10 bg-slate-950 px-3 py-2" type="number" step="0.01" value={form.riskLimit} onChange={(e) => setForm((prev) => ({ ...prev, riskLimit: Number(e.target.value) }))} />
        </label>
        <label className="space-y-2 text-sm">
          <span className="text-slate-300">Monitoring threshold</span>
          <input className="w-full rounded-lg border border-white/10 bg-slate-950 px-3 py-2" type="number" step="0.01" value={form.monitoringThreshold} onChange={(e) => setForm((prev) => ({ ...prev, monitoringThreshold: Number(e.target.value) }))} />
        </label>
        <label className="space-y-2 text-sm">
          <span className="text-slate-300">Execution mode</span>
          <select className="w-full rounded-lg border border-white/10 bg-slate-950 px-3 py-2" value={form.executionMode} onChange={(e) => setForm((prev) => ({ ...prev, executionMode: e.target.value as 'paper' | 'shadow' | 'live' }))}>
            <option value="paper">paper</option>
            <option value="shadow">shadow</option>
            <option value="live">live</option>
          </select>
        </label>
        <div className="md:col-span-2">
          <PermissionGate role={role} permission="config.edit">
            <ActionButton label={saveDraft.isPending ? 'Saving...' : 'Save Draft'} disabled={saveDraft.isPending} onClick={() => setConfirmOpen(true)} />
          </PermissionGate>
        </div>
      </div>
      <ConfirmModal
        open={confirmOpen}
        title="Save configuration draft"
        description="設定変更をドラフト保存します。監査ログへ記録され、権限チェックが適用されます。"
        pending={saveDraft.isPending}
        onClose={() => setConfirmOpen(false)}
        onConfirm={async () => {
          const result = await saveDraft.mutateAsync(form)
          setMessage(result.data.message)
          setConfirmOpen(false)
        }}
      />
    </div>
  )
}

'use client'

import { useMemo, useState } from 'react'
import { useCurrentUser, useStartStrategy, useStopStrategy, useStrategyRegistry, useUpdateStrategyRiskBudget } from '@/lib/api/hooks'
import { LoadingState } from '@/components/shared/loading-state'
import { ErrorState } from '@/components/shared/error-state'
import { ActionButton } from '@/components/shared/action-button'
import { MutationStatus } from '@/components/shared/mutation-status'
import { ConfirmModal } from '@/components/shared/confirm-modal'
import { PermissionGate } from '@/components/shared/permission-gate'
import { useUiStore } from '@/store/ui-store'
import { getArray, getRole } from '@/lib/api/normalize'

type StrategyAction = { type: 'start' | 'stop'; id: string; name: string } | null
type RiskEdit = { strategyId: string; value: string; name: string }

type StrategyRow = {
  id?: string
  name?: string
  mode?: string
  capitalAllocation?: number
  capitalPct?: number
  riskBudget?: number
  status?: string
  remote_status?: string
}

export default function StrategiesPage() {
  const strategiesQuery = useStrategyRegistry()
  const userQuery = useCurrentUser()
  const role = useUiStore((s) => s.roleOverride) ?? getRole(userQuery?.data)
  const start = useStartStrategy()
  const stop = useStopStrategy()
  const updateRisk = useUpdateStrategyRiskBudget()
  const [message, setMessage] = useState<string | null>(null)
  const [strategyAction, setStrategyAction] = useState<StrategyAction>(null)
  const [riskDrafts, setRiskDrafts] = useState<Record<string, string>>({})
  const pending = start.isPending || stop.isPending || updateRisk.isPending
  const description = useMemo(() => {
    if (!strategyAction) return ''
    return `Strategy ${strategyAction.name} を ${strategyAction.type === 'start' ? '開始' : '停止'}します。Command Center から監査ログへ記録されます。`
  }, [strategyAction])

  const strategies = getArray<StrategyRow>(strategiesQuery?.data)

  if (strategiesQuery?.isLoading) return <LoadingState />
  if (strategiesQuery?.isError) return <ErrorState message="Failed to load strategies." />

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Strategies</h1>
      <MutationStatus message={message} error={[start, stop, updateRisk].map((m) => (m.error instanceof Error ? m.error.message : null)).find(Boolean) || null} />
      <div className="overflow-hidden rounded-2xl border border-white/10 bg-slate-900/60">
        <table className="min-w-full text-sm">
          <thead className="bg-white/5 text-left text-slate-300">
            <tr>
              <th className="px-4 py-3">Strategy</th>
              <th className="px-4 py-3">Mode</th>
              <th className="px-4 py-3">Capital</th>
              <th className="px-4 py-3">Risk Budget</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {strategies.length === 0 ? (
              <tr>
                <td className="px-4 py-3 text-slate-400" colSpan={6}>No strategies</td>
              </tr>
            ) : (
              strategies.map((strategy, idx) => {
                const strategyId = strategy.id ?? strategy.name ?? `strategy-${idx}`
                const riskBudgetValue = riskDrafts[strategyId] ?? String(strategy.riskBudget ?? '')
                return (
                  <tr key={strategyId} className="border-t border-white/5">
                    <td className="px-4 py-3">{strategy.name ?? '-'}</td>
                    <td className="px-4 py-3">{strategy.mode ?? '-'}</td>
                    <td className="px-4 py-3">{strategy.capitalAllocation ?? strategy.capitalPct ?? '-'}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <input
                          className="w-24 rounded-lg border border-white/10 bg-slate-950 px-2 py-1 text-slate-100"
                          value={riskBudgetValue}
                          onChange={(e) => setRiskDrafts((drafts) => ({ ...drafts, [strategyId]: e.target.value }))}
                          placeholder="0.10"
                        />
                        <PermissionGate role={role} permission="strategy.control">
                          <ActionButton
                            label="Save"
                            disabled={pending || riskBudgetValue.length === 0}
                            onClick={async () => {
                              const next = Number(riskBudgetValue)
                              if (!Number.isFinite(next)) {
                                setMessage('Risk budget must be numeric.')
                                return
                              }
                              const result = await updateRisk.mutateAsync({ strategyId, riskBudget: next, note: 'Updated from Sprint6C UI' })
                              setMessage(result.data.message)
                            }}
                          />
                        </PermissionGate>
                      </div>
                    </td>
                    <td className="px-4 py-3 capitalize">{strategy.status ?? '-'}{strategy.remote_status ? ` / ${strategy.remote_status}` : ''}</td>
                    <td className="px-4 py-3">
                      <PermissionGate role={role} permission="strategy.control">
                        <div className="flex gap-2">
                          <ActionButton label="Start" disabled={pending} onClick={() => setStrategyAction({ type: 'start', id: strategyId, name: strategy.name ?? 'strategy' })} />
                          <ActionButton label="Stop" tone="danger" disabled={pending} onClick={() => setStrategyAction({ type: 'stop', id: strategyId, name: strategy.name ?? 'strategy' })} />
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
        open={!!strategyAction}
        title="Strategy action"
        description={description}
        tone={strategyAction?.type === 'stop' ? 'danger' : 'default'}
        confirmLabel={strategyAction?.type === 'stop' ? 'Stop' : 'Start'}
        pending={pending}
        onClose={() => setStrategyAction(null)}
        onConfirm={async () => {
          if (!strategyAction) return
          const result = strategyAction.type === 'start'
            ? await start.mutateAsync(strategyAction.id)
            : await stop.mutateAsync(strategyAction.id)
          setMessage(result.data.message)
          setStrategyAction(null)
        }}
      />
    </div>
  )
}

'use client'

import { useAuditLogs, useCurrentUser } from '@/lib/api/hooks'
import { LoadingState } from '@/components/shared/loading-state'
import { ErrorState } from '@/components/shared/error-state'
import { PermissionGate } from '@/components/shared/permission-gate'
import { useUiStore } from '@/store/ui-store'
import { getArray, getRole } from '@/lib/api/normalize'

const permissions = [
  ['viewer', '閲覧のみ'],
  ['operator', 'alerts / scheduler / strategy'],
  ['risk_manager', 'operator + governance'],
  ['admin', 'all + config'],
] as const

type AuditLogRow = {
  id?: string
  timestamp?: string
  createdAt?: string
  actor?: string
  role?: string
  action?: string
  target?: string
  status?: string
  detail?: string
}

export default function AdminPage() {
  const auditQuery = useAuditLogs()
  const userQuery = useCurrentUser()
  const role = useUiStore((s) => s.roleOverride) ?? getRole(userQuery?.data)

  const rows = getArray<AuditLogRow>(auditQuery?.data)

  if (auditQuery?.isLoading) return <LoadingState />
  if (auditQuery?.isError) return <ErrorState message="Failed to load audit logs." />

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Admin / Audit</h1>
        <p className="text-sm text-slate-400">RBAC マトリクスと監査ログを確認できます。</p>
      </div>

      <div className="grid gap-4 lg:grid-cols-[0.8fr,1.2fr]">
        <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-4">
          <h2 className="mb-3 text-lg font-semibold">Role Matrix</h2>
          <div className="space-y-2 text-sm">
            {permissions.map(([name, detail]) => (
              <div key={name} className="rounded-xl border border-white/10 bg-white/5 p-3">
                <div className="font-medium capitalize">{name}</div>
                <div className="text-slate-400">{detail}</div>
              </div>
            ))}
          </div>
        </div>

        <PermissionGate role={role} permission="audit.read">
          <div className="overflow-hidden rounded-2xl border border-white/10 bg-slate-900/60">
            <div className="border-b border-white/10 px-4 py-3 text-lg font-semibold">Audit Logs</div>
            <table className="min-w-full text-sm">
              <thead className="bg-white/5 text-left text-slate-300">
                <tr>
                  <th className="px-4 py-3">Time</th>
                  <th className="px-4 py-3">Actor</th>
                  <th className="px-4 py-3">Role</th>
                  <th className="px-4 py-3">Action</th>
                  <th className="px-4 py-3">Target</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {rows.length === 0 ? (
                  <tr>
                    <td className="px-4 py-3 text-slate-400" colSpan={6}>No audit logs</td>
                  </tr>
                ) : (
                  rows.map((row, idx) => (
                    <tr key={row.id ?? `${row.action ?? 'audit'}-${idx}`} className="border-t border-white/5">
                      <td className="px-4 py-3">{row.timestamp || row.createdAt ? new Date((row.timestamp ?? row.createdAt) as string).toLocaleString() : '-'}</td>
                      <td className="px-4 py-3">{row.actor ?? '-'}</td>
                      <td className="px-4 py-3 capitalize">{row.role ?? '-'}</td>
                      <td className="px-4 py-3">{row.action ?? '-'}</td>
                      <td className="px-4 py-3">{row.target ?? '-'}</td>
                      <td className="px-4 py-3 capitalize">{row.status ?? '-'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </PermissionGate>
      </div>
    </div>
  )
}

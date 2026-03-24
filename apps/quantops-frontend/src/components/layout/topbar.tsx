'use client';

import { useAlerts, useCurrentUser, useMonitoringSystem, useRiskSnapshot } from '@/lib/api/hooks';
import { usePathname } from 'next/navigation';
import { useUiStore } from '@/store/ui-store';

export function Topbar() {
  const pathname = usePathname();
  const isOverviewPage = pathname === '/';
  const environment = useUiStore((s) => s.environment);
  const setEnvironment = useUiStore((s) => s.setEnvironment);
  const roleOverride = useUiStore((s) => s.roleOverride);
  const setRoleOverride = useUiStore((s) => s.setRoleOverride);
  const { data } = useCurrentUser();
  const monitoring = useMonitoringSystem(!isOverviewPage);
  const alerts = useAlerts(!isOverviewPage);
  const risk = useRiskSnapshot(!isOverviewPage);
  const user = data?.data;
  const effectiveRole = roleOverride ?? user?.role ?? 'viewer';
  const monitoringData = monitoring.data?.data;
  const openAlerts = (alerts.data?.data ?? []).filter((item) => item.status === 'open');
  const criticalOpenAlerts = openAlerts.filter((item) => item.severity === 'critical');
  const riskData = risk.data?.data;
  const riskHalted = ['halted', 'paused'].includes((riskData?.tradingState || monitoringData?.riskTradingState || '').toLowerCase());
  const killSwitchTriggered = (riskData?.killSwitch || monitoringData?.killSwitch || '').toLowerCase() === 'triggered';
  const systemPill = isOverviewPage
    ? { label: 'Overview Focus', className: 'rounded-full border border-white/10 bg-white/5 px-3 py-2 text-slate-300' }
    : criticalOpenAlerts.length > 0
    ? { label: `Critical Alerts ${criticalOpenAlerts.length}`, className: 'rounded-full bg-rose-500/10 px-3 py-2 text-rose-300' }
    : riskHalted || killSwitchTriggered
      ? { label: killSwitchTriggered ? 'Risk Halted · Kill Switch' : 'Risk Halted', className: 'rounded-full bg-rose-500/10 px-3 py-2 text-rose-300' }
      : ['halted', 'blocked', 'degraded'].includes((monitoringData?.executionState || '').toLowerCase())
        ? { label: `Execution ${monitoringData?.executionState ?? 'degraded'}`, className: 'rounded-full bg-amber-500/10 px-3 py-2 text-amber-300' }
        : monitoringData?.workerStatus === 'degraded'
          ? { label: 'System Degraded', className: 'rounded-full bg-amber-500/10 px-3 py-2 text-amber-300' }
          : { label: 'System OK', className: 'rounded-full bg-emerald-500/10 px-3 py-2 text-emerald-300' };

  return (
    <header className="sticky top-0 z-10 flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 bg-slate-950/95 px-4 py-3 backdrop-blur">
      <div>
        <div className="text-sm text-slate-400">Sprint5 Dashboard</div>
        <div className="text-lg font-semibold">QuantOps Command Center</div>
      </div>
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <select
          className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={environment}
          onChange={(e) => setEnvironment(e.target.value as 'PAPER' | 'SHADOW' | 'LIVE')}
        >
          <option value="PAPER">PAPER</option>
          <option value="SHADOW">SHADOW</option>
          <option value="LIVE">LIVE</option>
        </select>
        <select
          className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={effectiveRole}
          onChange={(e) => setRoleOverride(e.target.value as typeof effectiveRole)}
          title="Demo role switcher"
        >
          <option value="viewer">viewer</option>
          <option value="operator">operator</option>
          <option value="risk_manager">risk_manager</option>
          <option value="admin">admin</option>
        </select>
        <div className="rounded-full border border-white/10 bg-white/5 px-3 py-2 text-slate-200">
          {user?.name ?? 'Operator'} · {effectiveRole}
        </div>
        <div className={systemPill.className}>{systemPill.label}</div>
      </div>
    </header>
  );
}


// Sprint6E note: write actions are enforced server-side via X-User-Role / X-User-Id headers.

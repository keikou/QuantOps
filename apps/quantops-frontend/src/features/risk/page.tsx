'use client';

import { useState } from 'react';
import { KpiCard } from '@/components/cards/kpi-card';
import { DataStatusBanner, DataStatusPill, resolveDataStatus } from '@/components/shared/data-status';
import { ErrorState } from '@/components/shared/error-state';
import { LoadingState } from '@/components/shared/loading-state';
import { ActionButton } from '@/components/shared/action-button';
import { MutationStatus } from '@/components/shared/mutation-status';
import { useKillSwitch, usePauseTrading, useResumeTrading, useRiskSnapshot } from '@/lib/api/hooks';
import type { RiskSnapshot } from '@/types/api';

const EMPTY_RISK: RiskSnapshot = {
  grossExposure: 0,
  netExposure: 0,
  var1d: 0,
  drawdown: 0,
  concentration: 0,
  killSwitch: 'normal',
  tradingState: 'running',
};

export default function RiskPage() {
  const risk = useRiskSnapshot();
  const pause = usePauseTrading();
  const resume = useResumeTrading();
  const killSwitch = useKillSwitch();
  const [message, setMessage] = useState<string | null>(null);

  const riskEnvelope = risk.data;
  const hasRiskData = Boolean(riskEnvelope && 'data' in riskEnvelope && riskEnvelope.data);
  if (risk.isLoading && !hasRiskData) return <LoadingState />;
  if (risk.error && !hasRiskData) return <ErrorState message="Risk snapshot load failed" />;
  const data = hasRiskData ? riskEnvelope!.data : EMPTY_RISK;
  const riskStatus = resolveDataStatus({ status: data.dataStatus, isLoading: risk.isLoading, hasData: hasRiskData, error: risk.error });
  const pending = pause.isPending || resume.isPending || killSwitch.isPending;
  const error = [pause, resume, killSwitch].map((m) => (m.error instanceof Error ? m.error.message : null)).find(Boolean) || null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <h1 className="section-title">Risk</h1>
        <DataStatusPill label="Risk" status={riskStatus} />
      </div>
      <MutationStatus message={message} error={error} />
      <DataStatusBanner label="Risk Snapshot" status={riskStatus} reason={data.statusReason} asOf={data.asOf} />
      <div className="page-grid">
        <KpiCard title="Gross Exposure" value={data.grossExposure} />
        <KpiCard title="Net Exposure" value={data.netExposure} />
        <KpiCard title="VaR 1d" value={data.var1d} />
        <KpiCard title="Drawdown" value={data.drawdown} />
      </div>
      <div className="card space-y-4 p-6 text-slate-300">
        <div>Kill Switch: <span className="font-semibold">{data.killSwitch}</span></div>
        <div>Trading State: <span className="font-semibold">{data.tradingState ?? 'running'}</span></div>
        <div>Concentration: {data.concentration}</div>
        <div>Alert: {data.alert ?? 'unknown'}</div>
        <div>Data Source: {data.dataSource ?? '-'}</div>
        <div className="flex flex-wrap gap-2">
          <ActionButton label="Pause Trading" disabled={pending} onClick={async () => { const result = await pause.mutateAsync({ note: 'Paused from Sprint6F risk page' }); setMessage(result.data.message); }} />
          <ActionButton label="Resume Trading" disabled={pending} onClick={async () => { const result = await resume.mutateAsync({ note: 'Resumed from Sprint6F risk page' }); setMessage(result.data.message); }} />
          <ActionButton label="Kill Switch" tone="danger" disabled={pending} onClick={async () => { const result = await killSwitch.mutateAsync({ note: 'Kill switch triggered from Sprint6F risk page' }); setMessage(result.data.message); }} />
        </div>
      </div>
    </div>
  );
}

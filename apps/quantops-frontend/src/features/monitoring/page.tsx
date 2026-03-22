'use client';

import { KpiCard } from '@/components/cards/kpi-card';
import { DataStatusBanner, DataStatusPill, resolveDataStatus } from '@/components/shared/data-status';
import { ErrorState } from '@/components/shared/error-state';
import { LoadingState } from '@/components/shared/loading-state';
import { useMonitoringSystem } from '@/lib/api/hooks';
import type { MonitoringSystem } from '@/types/api';

const EMPTY_MONITORING: MonitoringSystem = {
  cpu: 0,
  memory: 0,
  disk: '-',
  dbWritable: false,
  exchangeLatencyMs: 0,
  dataFreshnessSec: 0,
};

export default function MonitoringPage() {
  const monitoring = useMonitoringSystem();
  const monitoringEnvelope = monitoring.data;
  const hasMonitoringData = Boolean(monitoringEnvelope && 'data' in monitoringEnvelope && monitoringEnvelope.data);
  if (monitoring.isLoading && !hasMonitoringData) return <LoadingState />;
  if (monitoring.error && !hasMonitoringData) return <ErrorState message="Monitoring load failed" />;
  const data = hasMonitoringData ? monitoringEnvelope!.data : EMPTY_MONITORING;
  const monitoringStatus = resolveDataStatus({ status: data.dataStatus, isLoading: monitoring.isLoading, hasData: hasMonitoringData, error: monitoring.error });
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <h1 className="section-title">Monitoring</h1>
        <DataStatusPill label="Monitoring" status={monitoringStatus} />
      </div>
      <DataStatusBanner label="Monitoring Snapshot" status={monitoringStatus} reason={data.statusReason} asOf={data.asOf} />
      <div className="page-grid">
        <KpiCard title="CPU" value={`${Math.round(data.cpu * 100)}%`} />
        <KpiCard title="Memory" value={`${Math.round(data.memory * 100)}%`} />
        <KpiCard title="Exchange Latency" value={`${data.exchangeLatencyMs} ms`} />
        <KpiCard title="Data Freshness" value={`${Math.round(data.dataFreshnessSec)} sec`} />
      </div>
      <div className="card p-6 text-slate-300">
        Disk: {data.disk}<br />
        DB Writable: {String(data.dbWritable)}<br />
        Worker Status: {data.workerStatus || '-'}<br />
        Data Source: {data.dataSource || '-'}<br />
        Snapshot As Of: {data.asOf || '-'}
      </div>
    </div>
  );
}

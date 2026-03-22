import { formatNumber } from '@/lib/utils';

export function KpiCard({ title, value, subtitle }: { title: string; value: number | string; subtitle?: string }) {
  const display = typeof value === 'number' ? formatNumber(value) : value;
  return (
    <div className="card p-4">
      <div className="text-sm text-slate-400">{title}</div>
      <div className="mt-2 text-2xl font-semibold">{display}</div>
      {subtitle ? <div className="mt-1 text-xs text-slate-500">{subtitle}</div> : null}
    </div>
  );
}

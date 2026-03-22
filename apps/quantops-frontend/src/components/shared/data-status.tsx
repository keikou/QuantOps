import type { DataStatus } from '@/types/api';

function normalizeStatus(status?: string | null): DataStatus {
  switch (status) {
    case 'ok':
    case 'loading':
    case 'stale':
    case 'timed_out':
    case 'no_data':
    case 'fallback':
      return status;
    default:
      return 'ok';
  }
}

function formatReason(reason?: string | null) {
  if (!reason) return '';
  return reason
    .split('_')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function statusClasses(status: DataStatus) {
  switch (status) {
    case 'ok':
      return 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200';
    case 'loading':
      return 'border-sky-500/30 bg-sky-500/10 text-sky-200';
    case 'stale':
      return 'border-amber-500/30 bg-amber-500/10 text-amber-200';
    case 'timed_out':
      return 'border-rose-500/30 bg-rose-500/10 text-rose-200';
    case 'no_data':
      return 'border-slate-500/30 bg-slate-500/10 text-slate-200';
    case 'fallback':
      return 'border-orange-500/30 bg-orange-500/10 text-orange-200';
  }
}

function statusLabel(status: DataStatus) {
  switch (status) {
    case 'ok':
      return 'OK';
    case 'loading':
      return 'Loading';
    case 'stale':
      return 'Stale';
    case 'timed_out':
      return 'Timed Out';
    case 'no_data':
      return 'No Data';
    case 'fallback':
      return 'Fallback';
  }
}

export function resolveDataStatus(params: { status?: string | null; isLoading?: boolean; hasData?: boolean; error?: unknown }): DataStatus {
  const explicit = params.status ? normalizeStatus(params.status) : null;
  if (explicit) return explicit;
  if (params.isLoading && !params.hasData) return 'loading';
  if (params.error && params.hasData) return 'stale';
  if (params.error) {
    const message = params.error instanceof Error ? params.error.message : String(params.error ?? '');
    return /timeout/i.test(message) ? 'timed_out' : 'no_data';
  }
  return params.hasData ? 'ok' : 'no_data';
}

export function DataStatusPill({ label, status }: { label: string; status?: string | null }) {
  const normalized = normalizeStatus(status);
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-medium ${statusClasses(normalized)}`}>
      {label}: {statusLabel(normalized)}
    </span>
  );
}

export function DataStatusBanner({
  label,
  status,
  reason,
  asOf,
}: {
  label: string;
  status?: string | null;
  reason?: string | null;
  asOf?: string | null;
}) {
  const normalized = normalizeStatus(status);
  if (normalized === 'ok' || normalized === 'loading') return null;

  const message = {
    stale: `${label} is showing the latest cached snapshot while refresh runs in the background.`,
    timed_out: `${label} refresh timed out. Showing the last known safe state.`,
    no_data: `${label} has no usable snapshot yet.`,
    fallback: `${label} is running on fallback-derived values.`,
    ok: '',
    loading: '',
  }[normalized];

  const reasonText = formatReason(reason);

  return (
    <div className={`rounded-2xl border px-4 py-3 text-sm ${statusClasses(normalized)}`}>
      <div className="font-medium">{label} Status: {statusLabel(normalized)}</div>
      <div className="mt-1">{message}</div>
      {reasonText || asOf ? (
        <div className="mt-1 text-xs opacity-80">
          {reasonText ? `reason=${reasonText}` : null}
          {reasonText && asOf ? ' · ' : null}
          {asOf ? `asOf=${asOf}` : null}
        </div>
      ) : null}
    </div>
  );
}

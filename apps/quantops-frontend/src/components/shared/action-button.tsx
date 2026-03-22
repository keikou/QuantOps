'use client';

type Props = {
  label: string;
  onClick: () => void;
  disabled?: boolean;
  tone?: 'default' | 'danger' | 'secondary';
};

export function ActionButton({ label, onClick, disabled, tone = 'default' }: Props) {
  const toneClass = tone === 'danger'
    ? 'border-red-500/40 bg-red-500/10 text-red-200 hover:bg-red-500/20'
    : tone === 'secondary'
    ? 'border-white/10 bg-white/5 text-slate-200 hover:bg-white/10'
    : 'border-emerald-500/40 bg-emerald-500/10 text-emerald-200 hover:bg-emerald-500/20';

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={`rounded-lg border px-3 py-1.5 text-sm transition disabled:cursor-not-allowed disabled:opacity-50 ${toneClass}`}
    >
      {label}
    </button>
  );
}

type Props = {
  message?: string | null;
  error?: string | null;
};

export function MutationStatus({ message, error }: Props) {
  if (!message && !error) return null;
  return (
    <div className={`rounded-xl border px-3 py-2 text-sm ${error ? 'border-red-500/30 bg-red-500/10 text-red-200' : 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200'}`}>
      {error || message}
    </div>
  );
}

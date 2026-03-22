'use client';

import { usePathname } from 'next/navigation';
import { useApiErrorStore } from '@/lib/api/error-store';

export function ApiDebugBanner() {
  const pathname = usePathname();
  const lastError = useApiErrorStore((s) => s.lastError);
  const clearLastError = useApiErrorStore((s) => s.clearLastError);

  if (!lastError) return null;
  if (pathname && lastError.page !== pathname) {
    // Keep showing cross-page errors too, but mark where they came from.
  }

  return (
    <div className="border-b border-amber-700/40 bg-amber-950/50 px-4 py-3 text-sm text-amber-100">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-1">
          <div className="font-semibold">API refresh failed</div>
          <div>
            {lastError.method} {lastError.path} · {lastError.kind}
            {lastError.status ? ` · ${lastError.status}${lastError.statusText ? ` ${lastError.statusText}` : ''}` : ''}
          </div>
          <div className="text-amber-200/90">{lastError.message}</div>
          <div className="text-xs text-amber-200/80">
            page={lastError.page} · duration={lastError.durationMs}ms
            {lastError.correlationId ? ` · requestId=${lastError.correlationId}` : ''}
          </div>
          {lastError.responseSnippet ? (
            <pre className="mt-2 max-h-32 overflow-auto rounded-md border border-amber-700/30 bg-black/20 p-2 text-xs whitespace-pre-wrap">
              {lastError.responseSnippet}
            </pre>
          ) : null}
        </div>
        <button
          type="button"
          className="rounded-md border border-amber-600/40 px-3 py-1 text-xs text-amber-100 hover:bg-amber-900/40"
          onClick={() => clearLastError()}
        >
          Dismiss
        </button>
      </div>
    </div>
  );
}

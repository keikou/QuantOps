'use client';

type FrontendTelemetryEvent = {
  event_type: string;
  trace_id?: string | null;
  request_id?: string | null;
  session_id?: string | null;
  page_path?: string | null;
  status?: string | null;
  action?: string | null;
  target?: string | null;
  timestamp?: string;
  details?: Record<string, unknown>;
};

const SESSION_STORAGE_KEY = 'quantops-session-id';
const TRACE_STORAGE_KEY = 'quantops-trace-id';
const PAGE_STORAGE_KEY = 'quantops-page-path';
const TELEMETRY_URL = '/api/v1/admin/frontend-events';

function randomId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function safeWindow(): Window | null {
  return typeof window === 'undefined' ? null : window;
}

function readSessionStorage(key: string): string | null {
  const win = safeWindow();
  if (!win) return null;
  try {
    return win.sessionStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeSessionStorage(key: string, value: string): void {
  const win = safeWindow();
  if (!win) return;
  try {
    win.sessionStorage.setItem(key, value);
  } catch {
    return;
  }
}

export function getTelemetrySessionId(): string {
  const existing = readSessionStorage(SESSION_STORAGE_KEY);
  if (existing) return existing;
  const created = randomId('sess');
  writeSessionStorage(SESSION_STORAGE_KEY, created);
  return created;
}

export function getCurrentTraceId(): string | null {
  return readSessionStorage(TRACE_STORAGE_KEY);
}

export function getCurrentPagePath(): string | null {
  return readSessionStorage(PAGE_STORAGE_KEY);
}

export function beginPageTrace(pagePath: string): string {
  const traceId = randomId('trace');
  writeSessionStorage(TRACE_STORAGE_KEY, traceId);
  writeSessionStorage(PAGE_STORAGE_KEY, pagePath);
  return traceId;
}

export async function emitFrontendTelemetry(event: FrontendTelemetryEvent): Promise<void> {
  const win = safeWindow();
  if (!win) return;
  const body = JSON.stringify({
    timestamp: new Date().toISOString(),
    session_id: getTelemetrySessionId(),
    trace_id: getCurrentTraceId(),
    page_path: getCurrentPagePath() ?? `${win.location.pathname}${win.location.search}`,
    ...event,
  });
  try {
    if (typeof navigator !== 'undefined' && typeof navigator.sendBeacon === 'function') {
      const blob = new Blob([body], { type: 'application/json' });
      if (navigator.sendBeacon(TELEMETRY_URL, blob)) {
        return;
      }
    }
    await fetch(TELEMETRY_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
      keepalive: true,
      cache: 'no-store',
    });
  } catch {
    return;
  }
}

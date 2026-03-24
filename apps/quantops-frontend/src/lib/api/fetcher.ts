import { API_BASE_URL, API_DEBUG_ERRORS, API_TIMEOUT_MS, ENABLE_MOCK_FALLBACK, USE_PROXY } from '@/lib/api/config';
import { useApiErrorStore, type ApiErrorEntry, type ApiErrorKind } from '@/lib/api/error-store';
import type { ActionResult, ApiEnvelope } from '@/types/api';

class ApiRequestError extends Error {
  kind: ApiErrorKind;
  path: string;
  requestUrl: string;
  method: string;
  page: string;
  durationMs: number;
  status?: number;
  statusText?: string;
  responseSnippet?: string;
  correlationId?: string;

  constructor(params: {
    kind: ApiErrorKind;
    path: string;
    requestUrl: string;
    method: string;
    page: string;
    durationMs: number;
    message: string;
    status?: number;
    statusText?: string;
    responseSnippet?: string;
    correlationId?: string;
  }) {
    super(params.message);
    this.name = 'ApiRequestError';
    this.kind = params.kind;
    this.path = params.path;
    this.requestUrl = params.requestUrl;
    this.method = params.method;
    this.page = params.page;
    this.durationMs = params.durationMs;
    this.status = params.status;
    this.statusText = params.statusText;
    this.responseSnippet = params.responseSnippet;
    this.correlationId = params.correlationId;
  }
}

function buildUrl(path: string) {
  return USE_PROXY ? `/api/proxy${path}` : `${API_BASE_URL}${path}`;
}

function timeoutForPath(path: string) {
  if (path === '/api/v1/dashboard/overview') return Math.max(API_TIMEOUT_MS, 35000);
  if (path === '/api/v1/command-center/runtime/latest') return Math.max(API_TIMEOUT_MS, 15000);
  if (path === '/api/v1/analytics/equity-history') return Math.max(API_TIMEOUT_MS, 30000);
  if (path === '/api/v1/risk/snapshot') return Math.max(API_TIMEOUT_MS, 15000);
  if (path === '/api/v1/monitoring/system') return Math.max(API_TIMEOUT_MS, 25000);
  if (path === '/api/v1/scheduler/jobs') return Math.max(API_TIMEOUT_MS, 15000);
  if (path === '/api/v1/alerts') return Math.max(API_TIMEOUT_MS, 12000);
  if (path === '/api/v1/auth/me') return Math.max(API_TIMEOUT_MS, 12000);
  if (path === '/api/v1/portfolio/positions') return Math.max(API_TIMEOUT_MS, 12000);
  if (path === '/api/v1/portfolio/overview') return Math.max(API_TIMEOUT_MS, 12000);
  return API_TIMEOUT_MS;
}

function getCurrentPage() {
  if (typeof window === 'undefined') return 'server';
  return `${window.location.pathname}${window.location.search}`;
}

function makeRequestId() {
  return `qo-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function toSnippet(text: string | undefined, max = 800) {
  if (!text) return undefined;
  const normalized = text.trim();
  if (!normalized) return undefined;
  return normalized.length <= max ? normalized : `${normalized.slice(0, max)}...`;
}

function reportClientError(entry: ApiErrorEntry) {
  useApiErrorStore.getState().reportError(entry);
  if (API_DEBUG_ERRORS && typeof console !== 'undefined') {
    console.error('[QuantOps API]', entry);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<ApiEnvelope<T>> {
  const controller = new AbortController();
  const requestTimeoutMs = timeoutForPath(path);
  const timeout = setTimeout(() => controller.abort(new DOMException(`Timed out after ${requestTimeoutMs}ms`, 'TimeoutError')), requestTimeoutMs);
  const started = Date.now();
  const requestUrl = buildUrl(path);
  const method = init?.method || 'GET';
  const page = getCurrentPage();
  const requestId = makeRequestId();

  try {
    const response = await fetch(requestUrl, {
      ...init,
      signal: controller.signal,
      cache: 'no-store',
      headers: {
        'Content-Type': 'application/json',
        'X-Client-Request-Id': requestId,
        ...(init?.headers || {}),
      },
    });
    const durationMs = Date.now() - started;
    const correlationId = response.headers.get('x-request-id') || requestId;
    const rawText = await response.text();
    const snippet = toSnippet(rawText);
    if (!response.ok) {
      throw new ApiRequestError({
        kind: 'http',
        path,
        requestUrl,
        method,
        page,
        durationMs,
        status: response.status,
        statusText: response.statusText,
        responseSnippet: snippet,
        correlationId,
        message: `HTTP ${response.status}${response.statusText ? ` ${response.statusText}` : ''} while requesting ${path}`,
      });
    }
    try {
      return JSON.parse(rawText) as ApiEnvelope<T>;
    } catch (error) {
      throw new ApiRequestError({
        kind: 'parse',
        path,
        requestUrl,
        method,
        page,
        durationMs,
        responseSnippet: snippet,
        correlationId,
        message: `Invalid JSON received from ${path}: ${error instanceof Error ? error.message : String(error)}`,
      });
    }
  } catch (error) {
    const durationMs = Date.now() - started;
    const err = error instanceof ApiRequestError
      ? error
      : error instanceof DOMException && (error.name === 'AbortError' || error.name === 'TimeoutError')
        ? new ApiRequestError({
            kind: error.name === 'TimeoutError' ? 'timeout' : 'abort',
            path,
            requestUrl,
            method,
            page,
            durationMs,
            correlationId: requestId,
            message: `${error.name === 'TimeoutError' ? 'Request timeout' : 'Request aborted'} for ${path} after ${durationMs}ms`,
          })
        : new ApiRequestError({
            kind: 'network',
            path,
            requestUrl,
            method,
            page,
            durationMs,
            correlationId: requestId,
            message: error instanceof Error ? error.message : `Network error while requesting ${path}`,
          });

    if (err.kind !== 'abort') {
      reportClientError({
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        path: err.path,
        requestUrl: err.requestUrl,
        method: err.method,
        page: err.page,
        kind: err.kind,
        message: err.message,
        status: err.status,
        statusText: err.statusText,
        responseSnippet: err.responseSnippet,
        correlationId: err.correlationId,
        durationMs: err.durationMs,
        createdAt: new Date().toISOString(),
      });
    }

    if (!init && ENABLE_MOCK_FALLBACK) {
      console.warn('[QuantOps API] mock fallback requested but disabled in Sprint6H-9.2.4 hardening path', { path, requestUrl });
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}

export async function apiFetch<T>(path: string): Promise<ApiEnvelope<T>> {
  return request<T>(path);
}

export async function apiMutate<T = ActionResult>(path: string, method: 'POST' | 'PATCH' | 'PUT' | 'DELETE' = 'POST', body?: unknown): Promise<ApiEnvelope<T>> {
  return request<T>(path, {
    method,
    body: body ? JSON.stringify(body) : undefined,
  });
}

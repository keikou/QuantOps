import { NextRequest, NextResponse } from 'next/server';
import { ENABLE_PROXY_MOCK } from '@/lib/api/config';
import { getMockResponse, applyMockMutation } from '@/lib/api/mock-server-state';

const BASE = (process.env.QUANTOPS_API_BASE_URL || 'http://127.0.0.1:8010').trim().replace(/\/+$/, '');
const PROXY_RETRY_DELAY_MS = 250;

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function isRetriableStatus(status: number) {
  return status === 502 || status === 503 || status === 504;
}

function makeRequestId(request: NextRequest) {
  return request.headers.get('x-client-request-id') || `proxy-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

async function forward(request: NextRequest, segments: string[]) {
  const upstream = `${BASE}/${segments.join('/')}${request.nextUrl.search}`;
  const method = request.method;
  const bodyText = method === 'GET' || method === 'HEAD' ? undefined : await request.text();
  const requestId = makeRequestId(request);
  const started = Date.now();
  const maxAttempts = method === 'GET' || method === 'HEAD' ? 2 : 1;

  try {
    let response: Response | null = null;
    let upstreamHeadersDurationMs = 0;
    let lastError: unknown;
    let attempts = 0;

    for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
      attempts = attempt;
      const upstreamStarted = Date.now();
      try {
        const candidate = await fetch(upstream, {
          method,
          headers: {
            'Content-Type': 'application/json',
            'X-Request-Id': requestId,
          },
          body: bodyText,
          cache: 'no-store',
        });
        upstreamHeadersDurationMs += Date.now() - upstreamStarted;
        if (attempt < maxAttempts && isRetriableStatus(candidate.status)) {
          await sleep(PROXY_RETRY_DELAY_MS);
          continue;
        }
        response = candidate;
        break;
      } catch (error) {
        upstreamHeadersDurationMs += Date.now() - upstreamStarted;
        lastError = error;
        if (attempt < maxAttempts) {
          await sleep(PROXY_RETRY_DELAY_MS);
          continue;
        }
      }
    }

    if (!response) {
      throw lastError instanceof Error ? lastError : new Error('Upstream request failed');
    }
    const text = await response.text();
    const totalDurationMs = Date.now() - started;
    const upstreamBodyDurationMs = Math.max(totalDurationMs - upstreamHeadersDurationMs, 0);
    return new NextResponse(text, {
      status: response.status,
      headers: {
        'Content-Type': response.headers.get('Content-Type') || 'application/json',
        'X-Request-Id': response.headers.get('X-Request-Id') || requestId,
        'X-Proxy-Upstream-Headers-Duration-Ms': String(upstreamHeadersDurationMs),
        'X-Proxy-Upstream-Body-Duration-Ms': String(upstreamBodyDurationMs),
        'X-Proxy-Total-Duration-Ms': String(totalDurationMs),
        'X-Proxy-Attempts': String(attempts),
        'X-QuantOps-Handler-Duration-Ms': response.headers.get('X-QuantOps-Handler-Duration-Ms') || '',
        'X-QuantOps-Serialization-Duration-Ms': response.headers.get('X-QuantOps-Serialization-Duration-Ms') || '',
        'X-QuantOps-Total-Duration-Ms': response.headers.get('X-QuantOps-Total-Duration-Ms') || '',
      },
    });
  } catch (error) {
    const durationMs = Date.now() - started;
    console.error('[QuantOps Proxy] upstream request failed', {
      requestId,
      method,
      upstream,
      durationMs,
      error: error instanceof Error ? error.message : String(error),
    });
    if (!ENABLE_PROXY_MOCK) {
      return NextResponse.json(
        {
          error: 'Upstream unavailable',
          detail: error instanceof Error ? error.message : String(error),
          upstream,
          method,
          requestId,
          durationMs,
        },
        { status: 502, headers: { 'X-Request-Id': requestId } }
      );
    }

    const path = `/${segments.join('/')}`;
    if (method === 'GET') {
      const mock = getMockResponse(path);
      if (mock) return NextResponse.json(mock, { headers: { 'X-Request-Id': requestId, 'X-Mock-Source': 'proxy' } });
    } else {
      const parsed = bodyText ? JSON.parse(bodyText) : undefined;
      const mock = await applyMockMutation(path, parsed);
      if (mock) return NextResponse.json(mock, { headers: { 'X-Request-Id': requestId, 'X-Mock-Source': 'proxy' } });
    }

    return NextResponse.json({ error: 'No mock route', path, requestId }, { status: 404, headers: { 'X-Request-Id': requestId } });
  }
}

export async function GET(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return forward(request, path);
}
export async function POST(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return forward(request, path);
}
export async function PATCH(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return forward(request, path);
}
export async function PUT(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return forward(request, path);
}
export async function DELETE(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return forward(request, path);
}

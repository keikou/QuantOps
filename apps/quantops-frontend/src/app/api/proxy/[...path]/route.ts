import { NextRequest, NextResponse } from 'next/server';
import { ENABLE_PROXY_MOCK } from '@/lib/api/config';
import { getMockResponse, applyMockMutation } from '@/lib/api/mock-server-state';

const BASE = process.env.QUANTOPS_API_BASE_URL || 'http://localhost:8010';

function makeRequestId(request: NextRequest) {
  return request.headers.get('x-client-request-id') || `proxy-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

async function forward(request: NextRequest, segments: string[]) {
  const upstream = `${BASE}/${segments.join('/')}${request.nextUrl.search}`;
  const method = request.method;
  const bodyText = method === 'GET' || method === 'HEAD' ? undefined : await request.text();
  const requestId = makeRequestId(request);
  const started = Date.now();

  try {
    const upstreamStarted = Date.now();
    const response = await fetch(upstream, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'X-Request-Id': requestId,
      },
      body: bodyText,
      cache: 'no-store',
    });
    const upstreamHeadersDurationMs = Date.now() - upstreamStarted;
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

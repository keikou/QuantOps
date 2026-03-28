'use client';

import { useEffect, useRef } from 'react';
import { usePathname, useSearchParams } from 'next/navigation';
import { beginPageTrace, emitFrontendTelemetry, getTelemetrySessionId } from '@/lib/api/telemetry';

export function FrontendTelemetry() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const initializedRef = useRef(false);

  useEffect(() => {
    if (initializedRef.current) return;
    initializedRef.current = true;
    void emitFrontendTelemetry({
      event_type: 'app_started',
      session_id: getTelemetrySessionId(),
      status: 'ok',
      details: {
        user_agent: typeof navigator !== 'undefined' ? navigator.userAgent : 'unknown',
      },
    });
  }, []);

  useEffect(() => {
    const query = searchParams?.toString();
    const pagePath = query ? `${pathname}?${query}` : pathname;
    const traceId = beginPageTrace(pagePath);
    void emitFrontendTelemetry({
      event_type: 'page_view',
      trace_id: traceId,
      page_path: pagePath,
      status: 'ok',
    });
  }, [pathname, searchParams]);

  useEffect(() => {
    const onUnhandledRejection = (event: PromiseRejectionEvent) => {
      void emitFrontendTelemetry({
        event_type: 'client_error',
        status: 'error',
        action: 'unhandled_rejection',
        details: {
          reason: String(event.reason),
        },
      });
    };
    const onWindowError = (event: ErrorEvent) => {
      void emitFrontendTelemetry({
        event_type: 'client_error',
        status: 'error',
        action: 'window_error',
        details: {
          message: event.message,
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno,
        },
      });
    };
    window.addEventListener('unhandledrejection', onUnhandledRejection);
    window.addEventListener('error', onWindowError);
    return () => {
      window.removeEventListener('unhandledrejection', onUnhandledRejection);
      window.removeEventListener('error', onWindowError);
    };
  }, []);

  return null;
}

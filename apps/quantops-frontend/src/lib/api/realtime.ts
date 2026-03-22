'use client';

import { API_BASE_URL } from '@/lib/api/config';
import type { CommandCenterRealtimeEvent } from '@/types/api';

type RealtimeStatus = 'connecting' | 'connected' | 'disconnected';

const WS_RECONNECT_DELAY_MS = 2000;

function normalizeBaseUrl(baseUrl: string): string {
  return baseUrl.replace(/\/+$/, '');
}

export function buildCommandCenterWebSocketUrl(): string {
  if (typeof window === 'undefined') {
    const base = normalizeBaseUrl(API_BASE_URL)
      .replace(/^https/i, 'wss')
      .replace(/^http/i, 'ws');
    return `${base}/api/v1/command-center/ws/events`;
  }

  const explicitWsUrl =
    process.env.NEXT_PUBLIC_QUANTOPS_WS_URL?.trim() ||
    process.env.NEXT_PUBLIC_WS_URL?.trim();

  if (explicitWsUrl) {
    const normalized = normalizeBaseUrl(explicitWsUrl);
    if (normalized.endsWith('/api/v1/command-center/ws/events')) {
      return normalized;
    }
    return `${normalized}/api/v1/command-center/ws/events`;
  }

  const base = normalizeBaseUrl(API_BASE_URL);

  if (/^https?:\/\//i.test(base)) {
    return `${base.replace(/^https/i, 'wss').replace(/^http/i, 'ws')}/api/v1/command-center/ws/events`;
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host =
    window.location.hostname ||
    'localhost';

  const port =
    process.env.NEXT_PUBLIC_QUANTOPS_WS_PORT?.trim() ||
    process.env.NEXT_PUBLIC_QUANTOPS_API_PORT?.trim() ||
    '8010';

  return `${protocol}//${host}:${port}/api/v1/command-center/ws/events`;
}

export function createCommandCenterEventStream(
  onEvent: (event: CommandCenterRealtimeEvent) => void,
  onStatus?: (status: RealtimeStatus) => void,
): WebSocket | null {
  if (typeof window === 'undefined') return null;

  let activeSocket: WebSocket | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let manuallyClosed = false;
  let hasOpenedAtLeastOnce = false;

  const clearReconnectTimer = () => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
  };

  const scheduleReconnect = () => {
    if (manuallyClosed || reconnectTimer) return;

    onStatus?.('connecting');

    reconnectTimer = setTimeout(() => {
      reconnectTimer = null;
      connect();
    }, WS_RECONNECT_DELAY_MS);
  };

  const connect = () => {
    clearReconnectTimer();

    const wsUrl = buildCommandCenterWebSocketUrl();
    onStatus?.('connecting');

    try {
      const socket = new WebSocket(wsUrl);
      activeSocket = socket;

      socket.onopen = () => {
        hasOpenedAtLeastOnce = true;
        onStatus?.('connected');
        console.log('[QuantOps WS] open:', wsUrl);
      };

      socket.onmessage = (message) => {
        try {
          const parsed = JSON.parse(message.data) as CommandCenterRealtimeEvent;
          onEvent(parsed);
        } catch (error) {
          console.warn('[QuantOps WS] malformed payload ignored:', error, message.data);
        }
      };

      socket.onerror = (error) => {
        console.warn('[QuantOps WS] error:', error);
        /**
         * onerror の時点では handshake 完了前か、close が後続で来るだけのこともあるので
         * ここで即 permanently disconnected に固定しない。
         */
        if (!hasOpenedAtLeastOnce) {
          onStatus?.('connecting');
        }
      };

      socket.onclose = (event) => {
        console.warn('[QuantOps WS] close:', {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean,
        });

        if (activeSocket === socket) {
          activeSocket = null;
        }

        if (manuallyClosed) {
          onStatus?.('disconnected');
          return;
        }

        onStatus?.('connecting');
        scheduleReconnect();
      };
    } catch (error) {
      console.error('[QuantOps WS] failed to create socket:', error);
      onStatus?.('connecting');
      scheduleReconnect();
    }
  };

  connect();

  /**
   * 既存呼び出し側との互換性のため WebSocket を返すが、
   * close() を横取りして「手動クローズ」の意図を保持する。
   */
  const controller = {
    close: (code?: number, reason?: string) => {
      manuallyClosed = true;
      clearReconnectTimer();

      if (activeSocket) {
        try {
          activeSocket.close(code, reason);
        } catch (error) {
          console.warn('[QuantOps WS] close failed:', error);
        }
      }

      activeSocket = null;
      onStatus?.('disconnected');
    },
  } as WebSocket;

  return controller;
}
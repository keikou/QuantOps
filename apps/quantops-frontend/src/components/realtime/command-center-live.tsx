'use client';

import { useEffect, useMemo, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { createCommandCenterEventStream } from '@/lib/api/realtime';
import type { CommandCenterRealtimeEvent } from '@/types/api';

function invalidateKeysForEvent(queryClient: ReturnType<typeof useQueryClient>, eventType: string) {
  const mapping: Record<string, string[][]> = {
    pnl_update: [['overview'], ['portfolio-overview']],
    execution_event: [['overview'], ['monitoring-system']],
    risk_alert: [['risk-snapshot'], ['alerts'], ['overview']],
    strategy_status: [['strategy-registry'], ['overview']],
    system_status: [['monitoring-system'], ['scheduler-jobs'], ['overview']],
  };

  for (const key of mapping[eventType] ?? []) {
    queryClient.invalidateQueries({ queryKey: key });
  }
}

export function CommandCenterLive() {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const [lastEvent, setLastEvent] = useState<CommandCenterRealtimeEvent | null>(null);

  useEffect(() => {
    const socket = createCommandCenterEventStream(
      (event) => {
        setLastEvent(event);
        if (event.event_type !== 'hello' && event.event_type !== 'heartbeat') {
          invalidateKeysForEvent(queryClient, event.event_type);
        }
      },
      setStatus,
    );

    return () => {
      socket?.close();
    };
  }, [queryClient]);

  const label = useMemo(() => {
    if (status === 'connected') return 'Live WS connected';
    if (status === 'connecting') return 'Live WS connecting';
    return 'Live WS disconnected';
  }, [status]);

  return (
    <div className="rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-2 text-cyan-200">
      {label}
      {lastEvent?.event_type ? ` · ${lastEvent.event_type}` : ''}
    </div>
  );
}

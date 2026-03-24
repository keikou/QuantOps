'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { createCommandCenterEventStream } from '@/lib/api/realtime';
import type { CommandCenterRealtimeEvent } from '@/types/api';

export type CommandCenterLiveEventType = Exclude<CommandCenterRealtimeEvent['event_type'], 'hello' | 'heartbeat'>;

type CommandCenterLiveProps = {
  eventTypes?: CommandCenterLiveEventType[];
  invalidateKeys?: Partial<Record<CommandCenterLiveEventType, string[][]>>;
  onEvent?: (event: CommandCenterRealtimeEvent) => void;
  showBadge?: boolean;
};

function invalidateKeysForEvent(
  queryClient: ReturnType<typeof useQueryClient>,
  eventType: CommandCenterLiveEventType,
  invalidateKeys?: Partial<Record<CommandCenterLiveEventType, string[][]>>,
) {
  for (const key of invalidateKeys?.[eventType] ?? []) {
    queryClient.invalidateQueries({ queryKey: key });
  }
}

export function CommandCenterLive({
  eventTypes,
  invalidateKeys,
  onEvent,
  showBadge = true,
}: CommandCenterLiveProps) {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const [lastEvent, setLastEvent] = useState<CommandCenterRealtimeEvent | null>(null);
  const eventTypesKey = useMemo(() => JSON.stringify(eventTypes ?? []), [eventTypes]);
  const eventTypeSet = useMemo(() => new Set(eventTypes ?? []), [eventTypesKey]);
  const onEventRef = useRef(onEvent);
  const invalidateKeysRef = useRef(invalidateKeys);

  useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  useEffect(() => {
    invalidateKeysRef.current = invalidateKeys;
  }, [invalidateKeys]);

  useEffect(() => {
    const socket = createCommandCenterEventStream(
      (event) => {
        setLastEvent(event);
        if (event.event_type === 'hello' || event.event_type === 'heartbeat') {
          return;
        }

        const typedEvent = event.event_type as CommandCenterLiveEventType;
        if (eventTypeSet.size > 0 && !eventTypeSet.has(typedEvent)) {
          return;
        }

        if (invalidateKeysRef.current) {
          invalidateKeysForEvent(queryClient, typedEvent, invalidateKeysRef.current);
        }

        onEventRef.current?.(event);
      },
      setStatus,
    );

    return () => {
      socket?.close();
    };
  }, [eventTypeSet, queryClient]);

  const label = useMemo(() => {
    if (status === 'connected') return 'Live WS connected';
    if (status === 'connecting') return 'Live WS connecting';
    return 'Live WS disconnected';
  }, [status]);

  if (!showBadge) return null;

  return (
    <div className="rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-2 text-cyan-200">
      {label}
      {lastEvent?.event_type ? ` | ${lastEvent.event_type}` : ''}
    </div>
  );
}

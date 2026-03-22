'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [client] = useState(() =>
    new QueryClient({
      defaultOptions: {
        queries: {
          retry: 1,
          staleTime: 5000,
          gcTime: 5 * 60 * 1000,
          refetchOnWindowFocus: false,
          refetchOnReconnect: true,
        },
      },
    })
  );
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

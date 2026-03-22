'use client';

import { create } from 'zustand';

export type ApiErrorKind = 'timeout' | 'abort' | 'network' | 'http' | 'parse' | 'unknown';

export type ApiErrorEntry = {
  id: string;
  path: string;
  requestUrl: string;
  method: string;
  page: string;
  kind: ApiErrorKind;
  message: string;
  status?: number;
  statusText?: string;
  responseSnippet?: string;
  correlationId?: string;
  durationMs: number;
  createdAt: string;
};

type ApiErrorStore = {
  lastError?: ApiErrorEntry;
  errors: ApiErrorEntry[];
  reportError: (entry: ApiErrorEntry) => void;
  clearLastError: () => void;
  clearAll: () => void;
};

export const useApiErrorStore = create<ApiErrorStore>((set) => ({
  lastError: undefined,
  errors: [],
  reportError: (entry) =>
    set((state) => ({
      lastError: entry,
      errors: [entry, ...state.errors].slice(0, 20),
    })),
  clearLastError: () => set((state) => ({ ...state, lastError: undefined })),
  clearAll: () => set({ lastError: undefined, errors: [] }),
}));

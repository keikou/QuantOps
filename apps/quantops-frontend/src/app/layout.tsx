import './globals.css';
import type { Metadata } from 'next';
import { Suspense } from 'react';
import { FrontendTelemetry } from '@/components/telemetry/frontend-telemetry';
import { QueryProvider } from '@/lib/api/query-provider';

export const metadata: Metadata = {
  title: 'QuantOps Sprint5 Frontend',
  description: 'Sprint5 QuantOps dashboard frontend scaffold',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body>
        <QueryProvider>
          <Suspense fallback={null}>
            <FrontendTelemetry />
          </Suspense>
          {children}
        </QueryProvider>
      </body>
    </html>
  );
}

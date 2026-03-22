import './globals.css';
import type { Metadata } from 'next';
import { QueryProvider } from '@/lib/api/query-provider';

export const metadata: Metadata = {
  title: 'QuantOps Sprint5 Frontend',
  description: 'Sprint5 QuantOps dashboard frontend scaffold',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body>
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}

import { Sidebar } from '@/components/layout/sidebar';
import { Topbar } from '@/components/layout/topbar';
import { ApiDebugBanner } from '@/components/shared/api-debug-banner';

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 lg:flex">
      <Sidebar />
      <div className="flex min-h-screen flex-1 flex-col">
        <Topbar />
        <ApiDebugBanner />
        <main className="flex-1 p-4 md:p-6">{children}</main>
      </div>
    </div>
  );
}

'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';

const items = [
  ['/', 'Overview'],
  ['/portfolio', 'Portfolio'],
  ['/strategies', 'Strategies'],
  ['/execution', 'Execution'],
  ['/risk', 'Risk'],
  ['/monitoring', 'Monitoring'],
  ['/alerts', 'Alerts'],
  ['/scheduler', 'Scheduler'],
  ['/research', 'Research'],
  ['/alpha-factory', 'Alpha Factory'],
  ['/governance', 'Governance'],
  ['/config', 'Config'],
  ['/admin', 'Admin / Audit'],
] as const;

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden w-64 shrink-0 border-r border-slate-800 bg-slate-950/80 px-3 py-4 lg:block">
      <div className="mb-2 px-3 text-xl font-semibold">QuantOps</div>
      <div className="mb-6 px-3 text-xs uppercase tracking-[0.2em] text-slate-500">Production Console</div>
      <nav className="space-y-1">
        {items.map(([href, label]) => (
          <Link
            key={href}
            href={href}
            className={cn(
              'block rounded-xl px-3 py-2 text-sm transition hover:bg-slate-800 hover:text-white',
              pathname === href ? 'bg-slate-800 text-white' : 'text-slate-300'
            )}
          >
            {label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}

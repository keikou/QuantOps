import type { ReactNode } from 'react';
import { hasPermission, type Permission } from '@/lib/auth/permissions';
import type { UserRole } from '@/types/api';

export function PermissionGate({
  role,
  permission,
  children,
  fallback,
}: {
  role?: UserRole;
  permission: Permission;
  children: ReactNode;
  fallback?: ReactNode;
}) {
  if (!hasPermission(role, permission)) {
    return fallback ?? <span className="text-xs text-slate-500">権限がありません</span>;
  }
  return <>{children}</>;
}

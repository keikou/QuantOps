import type { UserRole } from '@/types/api';

export type Permission =
  | 'alerts.ack'
  | 'scheduler.control'
  | 'strategy.control'
  | 'governance.review'
  | 'config.edit'
  | 'audit.read';

const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  viewer: ['audit.read'],
  operator: ['alerts.ack', 'scheduler.control', 'strategy.control', 'audit.read'],
  risk_manager: ['alerts.ack', 'scheduler.control', 'strategy.control', 'governance.review', 'audit.read'],
  admin: ['alerts.ack', 'scheduler.control', 'strategy.control', 'governance.review', 'config.edit', 'audit.read'],
};

export function hasPermission(role: UserRole | undefined, permission: Permission) {
  if (!role) return false;
  return ROLE_PERMISSIONS[role].includes(permission);
}

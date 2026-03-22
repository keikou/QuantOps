import { create } from 'zustand';
import type { UserRole } from '@/types/api';

type UiState = {
  environment: 'PAPER' | 'SHADOW' | 'LIVE';
  roleOverride: UserRole | null;
  setEnvironment: (environment: UiState['environment']) => void;
  setRoleOverride: (role: UserRole | null) => void;
};

export const useUiStore = create<UiState>((set) => ({
  environment: 'PAPER',
  roleOverride: null,
  setEnvironment: (environment) => set({ environment }),
  setRoleOverride: (roleOverride) => set({ roleOverride }),
}));

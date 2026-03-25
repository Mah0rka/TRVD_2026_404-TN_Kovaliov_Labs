// Модуль зберігає клієнтський стан і повʼязані з ним дії.

import { create } from "zustand";

import type { CurrentUser } from "../../../shared/api";

type AuthState = {
  user: CurrentUser | null;
  isAuthenticated: boolean;
  isReady: boolean;
  setUser: (user: CurrentUser) => void;
  setReady: () => void;
  clearAuth: () => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isReady: false,
  setUser: (user) => set({ user, isAuthenticated: true, isReady: true }),
  setReady: () => set({ isReady: true }),
  clearAuth: () => set({ user: null, isAuthenticated: false, isReady: true })
}));

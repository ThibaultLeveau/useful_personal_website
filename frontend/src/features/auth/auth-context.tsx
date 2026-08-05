"use client";

import { createContext, useContext } from "react";

import type { ChangePasswordRequest, LoginRequest, SessionData } from "@/generated/api/src/models";

export interface AuthContextValue {
  changePassword(request: ChangePasswordRequest): Promise<SessionData>;
  continueSession(): Promise<SessionData>;
  dismissExpiryWarning(): void;
  expireSession(): void;
  expiryWarning: boolean;
  login(request: LoginRequest): Promise<SessionData>;
  logout(): Promise<void>;
  logoutUnconfirmed: boolean;
  session: SessionData | null;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function useOptionalAuth(): AuthContextValue | null {
  return useContext(AuthContext);
}

export function useAuth(): AuthContextValue {
  const value = useOptionalAuth();
  if (!value) throw new Error("useAuth must be used inside AdminAuthBoundary.");
  return value;
}

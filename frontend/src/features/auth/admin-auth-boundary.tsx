"use client";

import type { Route } from "next";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

import { AdminShell } from "@/components/admin/admin-shell";
import { Button } from "@/components/ui/button";
import { LoadingPanel } from "@/components/ui/loading-panel";
import { SkipLink } from "@/components/ui/skip-link";
import type { ChangePasswordRequest, LoginRequest, SessionData } from "@/generated/api/src/models";
import { ApiError } from "@/lib/api";

import { createAuthApi, type AuthApiBoundary } from "./api";
import { AuthContext, type AuthContextValue } from "./auth-context";
import { AuthFrame } from "./auth-frame";
import styles from "./auth.module.css";
import { isExpiredAuthError } from "./auth-errors";
import {
  expiredPathFor,
  isSignedOutAuthRoute,
  loginPathFor,
  returnPathFromCurrentLocation,
} from "./safe-return";
import { SessionExpiryBanner } from "./session-expiry-banner";
import { SessionAccountActions } from "./session-account-actions";

const defaultApi = createAuthApi();
const EXPIRY_WARNING_MS = 2 * 60 * 1000;

type BoundaryState =
  | { status: "checking" }
  | { error: ApiError; status: "error" }
  | {
      session: SessionData | null;
      signedOutReason?: "expired" | "signed-out";
      status: "ready";
    };

export interface AdminAuthBoundaryProps {
  api?: AuthApiBoundary;
  children: ReactNode;
  now?: () => number;
}

export function AdminAuthBoundary({
  api = defaultApi,
  children,
  now = Date.now,
}: AdminAuthBoundaryProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [state, setState] = useState<BoundaryState>({ status: "checking" });
  const [expiryWarning, setExpiryWarning] = useState(false);
  const [logoutUnconfirmed, setLogoutUnconfirmed] = useState(false);
  const [checkSequence, setCheckSequence] = useState(0);

  const expire = useCallback(() => {
    setExpiryWarning(false);
    setState({ session: null, signedOutReason: "expired", status: "ready" });
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void api
      .getSession({ signal: controller.signal })
      .then((session) => setState({ session, status: "ready" }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        if (isExpiredAuthError(error))
          setState({ session: null, signedOutReason: "signed-out", status: "ready" });
        else
          setState({
            error:
              error instanceof ApiError
                ? error
                : new ApiError({
                    code: "API_CLIENT_ERROR",
                    message: "The API request failed safely.",
                    status: 0,
                  }),
            status: "error",
          });
      });
    return () => controller.abort();
  }, [api, checkSequence]);

  const session = state.status === "ready" ? state.session : null;

  useEffect(() => {
    if (!session) return;
    const expiresAt = Math.min(
      session.idleExpiresAt.getTime(),
      session.absoluteExpiresAt.getTime(),
    );
    const warningDelay = expiresAt - EXPIRY_WARNING_MS - now();
    const expiryDelay = expiresAt - now();
    const warningTimer = window.setTimeout(() => setExpiryWarning(true), Math.max(0, warningDelay));
    const expiryTimer = window.setTimeout(expire, Math.max(0, expiryDelay));
    return () => {
      window.clearTimeout(warningTimer);
      window.clearTimeout(expiryTimer);
    };
  }, [expire, now, session]);

  useEffect(() => {
    if (state.status !== "ready") return;
    if (!state.session) {
      if (!isSignedOutAuthRoute(pathname)) {
        router.replace(
          (state.signedOutReason === "expired"
            ? expiredPathFor(pathname)
            : loginPathFor(pathname)) as Route,
        );
      }
      return;
    }
    if (state.session.mustChangePassword && pathname !== "/admin/change-password") {
      router.replace("/admin/change-password" as Route);
      return;
    }
    if (!state.session.mustChangePassword && isSignedOutAuthRoute(pathname)) {
      router.replace(returnPathFromCurrentLocation() as Route);
    }
  }, [pathname, router, state]);

  const context = useMemo<AuthContextValue | null>(() => {
    if (!session) return null;
    return {
      session,
      expiryWarning,
      logoutUnconfirmed,
      dismissExpiryWarning: () => setExpiryWarning(false),
      expireSession: expire,
      login: async (request: LoginRequest) => {
        const next = await api.login(request);
        setLogoutUnconfirmed(false);
        setState({ session: next, status: "ready" });
        return next;
      },
      changePassword: async (request: ChangePasswordRequest) => {
        try {
          const next = await api.changePassword(request);
          setState({ session: next, status: "ready" });
          return next;
        } catch (error) {
          if (isExpiredAuthError(error)) expire();
          throw error;
        }
      },
      continueSession: async () => {
        try {
          const next = await api.refreshSession();
          setExpiryWarning(false);
          setState({ session: next, status: "ready" });
          return next;
        } catch (error) {
          if (isExpiredAuthError(error)) expire();
          throw error;
        }
      },
      logout: async () => {
        setExpiryWarning(false);
        setState({ session: null, signedOutReason: "signed-out", status: "ready" });
        router.replace("/admin/login" as Route);
        try {
          await api.logout();
          setLogoutUnconfirmed(false);
        } catch {
          setLogoutUnconfirmed(true);
        }
      },
    };
  }, [api, expire, expiryWarning, logoutUnconfirmed, router, session]);

  if (state.status === "checking") {
    return (
      <AuthFrame>
        <main className={styles.authMain} id="auth-main" tabIndex={-1}>
          <LoadingPanel label="Checking the protected administrator session" />
        </main>
      </AuthFrame>
    );
  }

  if (state.status === "error" && !isSignedOutAuthRoute(pathname)) {
    return (
      <AuthFrame>
        <main className={styles.authMain} id="auth-main" tabIndex={-1}>
          <section aria-labelledby="session-check-title" className={styles.authCard}>
            <p className="eyebrow">Administration / Connection</p>
            <h1 id="session-check-title">The session could not be checked</h1>
            <p>Protected content remains hidden. Check the connection and try again.</p>
            {state.error.requestId ? (
              <p className={styles.requestId}>Request ID: {state.error.requestId}</p>
            ) : null}
            <Button
              onClick={() => {
                setState({ status: "checking" });
                setCheckSequence((value) => value + 1);
              }}
            >
              Try again
            </Button>
          </section>
        </main>
      </AuthFrame>
    );
  }

  if (!session) {
    if (!isSignedOutAuthRoute(pathname)) {
      return (
        <AuthFrame>
          <main className={styles.authMain} id="auth-main" tabIndex={-1}>
            <p aria-live="polite" role="status">
              Redirecting to secure sign in…
            </p>
          </main>
        </AuthFrame>
      );
    }
    const signedOutContext: AuthContextValue = {
      session: null,
      expiryWarning: false,
      logoutUnconfirmed,
      dismissExpiryWarning: () => undefined,
      expireSession: expire,
      changePassword: async () => {
        throw new ApiError({
          code: "AUTHENTICATION_REQUIRED",
          message: "Authentication is required.",
          status: 401,
        });
      },
      continueSession: async () => {
        throw new ApiError({
          code: "AUTHENTICATION_REQUIRED",
          message: "Authentication is required.",
          status: 401,
        });
      },
      login: async (request) => {
        const next = await api.login(request);
        setLogoutUnconfirmed(false);
        setState({ session: next, status: "ready" });
        return next;
      },
      logout: async () => {
        try {
          await api.logout();
          setLogoutUnconfirmed(false);
        } catch {
          setLogoutUnconfirmed(true);
        }
      },
    };
    return (
      <AuthContext.Provider value={signedOutContext}>
        <AuthFrame>{children}</AuthFrame>
      </AuthContext.Provider>
    );
  }

  if (
    (session.mustChangePassword && pathname !== "/admin/change-password") ||
    (!session.mustChangePassword && isSignedOutAuthRoute(pathname))
  ) {
    return (
      <AuthFrame>
        <main className={styles.authMain} id="auth-main" tabIndex={-1}>
          <p aria-live="polite" role="status">
            Redirecting securely…
          </p>
        </main>
      </AuthFrame>
    );
  }

  if (!context) return null;

  if (session.mustChangePassword) {
    return (
      <AuthContext.Provider value={context}>
        <AuthFrame>{children}</AuthFrame>
      </AuthContext.Provider>
    );
  }

  return (
    <AuthContext.Provider value={context}>
      <SkipLink href="#admin-main" label="Skip to administration content" />
      <AdminShell>
        <SessionAccountActions />
        <SessionExpiryBanner />
        {children}
      </AdminShell>
    </AuthContext.Provider>
  );
}

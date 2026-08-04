"use client";

import type { Route } from "next";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Surface } from "@/components/ui/surface";
import type { ChangePasswordRequest, LoginRequest } from "@/generated/api/src/models";

import { useAuth } from "./auth-context";
import styles from "./auth.module.css";
import { ChangePasswordForm } from "./change-password-form";
import { LoginForm } from "./login-form";

function AuthPageHeader({
  eyebrow,
  title,
  description,
}: Record<"description" | "eyebrow" | "title", string>) {
  return (
    <header className={styles.authHeader}>
      <p className="eyebrow">{eyebrow}</p>
      <h1>{title}</h1>
      <p>{description}</p>
    </header>
  );
}

export function LoginScreen() {
  const { login, logout, logoutUnconfirmed } = useAuth();
  const [retryingLogout, setRetryingLogout] = useState(false);

  async function signIn(request: LoginRequest) {
    await login(request);
  }

  return (
    <main className={styles.authMain} id="auth-main" tabIndex={-1}>
      <Surface className={styles.authCard}>
        <AuthPageHeader
          description="Use the administrator account provisioned through the explicit bootstrap process."
          eyebrow="Administration / Secure access"
          title="Sign in"
        />
        <LoginForm onLogin={signIn} />
        {logoutUnconfirmed ? (
          <section aria-labelledby="logout-warning-title" className={styles.logoutWarning}>
            <h2 id="logout-warning-title">Server sign-out was not confirmed</h2>
            <p>
              Protected content was cleared from this page, but the server could not be reached.
              Retry before leaving this device.
            </p>
            <Button
              disabled={retryingLogout}
              onClick={async () => {
                setRetryingLogout(true);
                await logout();
                setRetryingLogout(false);
              }}
              variant="secondary"
            >
              {retryingLogout ? "Retrying sign out…" : "Retry server sign out"}
            </Button>
          </section>
        ) : null}
        <p className={styles.securityNote}>
          Sign-in errors do not disclose whether an account exists. Credentials are sent only to the
          same-origin authentication API and are never stored by this interface.
        </p>
      </Surface>
    </main>
  );
}

export function ChangePasswordScreen() {
  const { changePassword, logout, session } = useAuth();
  const router = useRouter();

  if (!session) return null;
  const mustChangePassword = session.mustChangePassword;

  async function submit(request: ChangePasswordRequest) {
    await changePassword(request);
    if (mustChangePassword) router.replace("/admin" as Route);
  }

  return (
    <main
      className={mustChangePassword ? styles.authMain : "admin-main"}
      id={mustChangePassword ? "auth-main" : "admin-main"}
      tabIndex={-1}
    >
      <Surface className={styles.authCard}>
        <AuthPageHeader
          description={
            mustChangePassword
              ? "Replace the initial credential before entering the administration workspace."
              : "Changing your password revokes other sessions and rotates this protected session."
          }
          eyebrow={mustChangePassword ? "Required setup" : "Account security"}
          title={mustChangePassword ? "Set a private password" : "Change password"}
        />
        <ChangePasswordForm
          forced={mustChangePassword}
          onChangePassword={submit}
          onLogout={logout}
        />
      </Surface>
    </main>
  );
}

function formatDate(value: Date): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(value);
}

export function AccountScreen() {
  const { continueSession, logout, session } = useAuth();
  const [refreshing, setRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState(false);

  if (!session) return null;

  async function refresh() {
    setRefreshing(true);
    setRefreshError(false);
    try {
      await continueSession();
    } catch {
      setRefreshError(true);
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <main className="admin-main" id="admin-main" tabIndex={-1}>
      <header className="admin-page-header">
        <p className="eyebrow">Account / Current session</p>
        <h1>Account security</h1>
      </header>
      <Surface className={styles.accountCard}>
        <div>
          <p className={styles.metaLabel}>Signed in as</p>
          <h2>{session.displayName}</h2>
        </div>
        <dl className={styles.sessionFacts}>
          <div>
            <dt>Idle expiry</dt>
            <dd>
              <time dateTime={session.idleExpiresAt.toISOString()}>
                {formatDate(session.idleExpiresAt)}
              </time>
            </dd>
          </div>
          <div>
            <dt>Absolute expiry</dt>
            <dd>
              <time dateTime={session.absoluteExpiresAt.toISOString()}>
                {formatDate(session.absoluteExpiresAt)}
              </time>
            </dd>
          </div>
        </dl>
        {refreshError ? (
          <p className={styles.inlineError} role="alert">
            The session could not be continued. Check the connection and try again.
          </p>
        ) : null}
        <div className={styles.actions}>
          <Button disabled={refreshing} onClick={refresh}>
            {refreshing ? "Continuing…" : "Continue session"}
          </Button>
          <Link className="button button--secondary" href={"/admin/change-password" as Route}>
            Change password
          </Link>
          <Button onClick={logout} variant="quiet">
            Sign out
          </Button>
        </div>
      </Surface>
    </main>
  );
}

export function SessionExpiredScreen() {
  return (
    <main className={styles.authMain} id="auth-main" tabIndex={-1}>
      <Surface className={styles.authCard}>
        <AuthPageHeader
          description="Protected content has been removed from this page. Sign in again to continue safely."
          eyebrow="Administration / Session ended"
          title="Your session has expired"
        />
        <Link className="button button--primary" href={"/admin/login" as Route}>
          Sign in again
        </Link>
        <p className={styles.securityNote}>
          Unsaved changes may need to be entered again. No credential fields or protected page data
          were preserved here.
        </p>
      </Surface>
    </main>
  );
}

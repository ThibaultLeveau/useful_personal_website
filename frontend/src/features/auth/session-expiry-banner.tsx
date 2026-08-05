"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";

import { useAuth } from "./auth-context";
import styles from "./auth.module.css";

export function SessionExpiryBanner() {
  const { continueSession, dismissExpiryWarning, expiryWarning } = useAuth();
  const [refreshing, setRefreshing] = useState(false);
  const [failed, setFailed] = useState(false);

  if (!expiryWarning) return null;

  async function refresh() {
    setRefreshing(true);
    setFailed(false);
    try {
      await continueSession();
    } catch {
      setFailed(true);
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <section aria-labelledby="session-warning-title" className={styles.sessionWarning}>
      <div>
        <h2 id="session-warning-title">Your session will expire soon</h2>
        <p>
          Continue the session to keep working. Unsaved work is not promised until its server save
          succeeds.
        </p>
        {failed ? <p role="alert">The session could not be continued. Try again.</p> : null}
      </div>
      <div className={styles.actions}>
        <Button disabled={refreshing} onClick={refresh}>
          {refreshing ? "Continuing…" : "Continue session"}
        </Button>
        <Button onClick={dismissExpiryWarning} variant="quiet">
          Dismiss
        </Button>
      </div>
    </section>
  );
}

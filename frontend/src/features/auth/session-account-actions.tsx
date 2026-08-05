"use client";

import type { Route } from "next";
import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";

import { useAuth } from "./auth-context";
import styles from "./auth.module.css";

export function SessionAccountActions() {
  const { logout, session } = useAuth();
  const [loggingOut, setLoggingOut] = useState(false);

  if (!session) return null;

  async function signOut() {
    setLoggingOut(true);
    await logout();
  }

  return (
    <section aria-label="Administrator session" className={styles.accountActions}>
      <p>
        Signed in as <strong>{session.displayName}</strong>
      </p>
      <div className={styles.actions}>
        <Link className="button button--secondary" href={"/admin/account" as Route}>
          Account
        </Link>
        <Button disabled={loggingOut} onClick={signOut} variant="quiet">
          {loggingOut ? "Clearing session…" : "Sign out"}
        </Button>
      </div>
    </section>
  );
}

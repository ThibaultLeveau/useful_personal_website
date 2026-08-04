import Link from "next/link";
import type { ReactNode } from "react";

import { SkipLink } from "@/components/ui/skip-link";
import { ThemeSelector } from "@/components/ui/theme-selector";

import styles from "./auth.module.css";

export function AuthFrame({ children }: { children: ReactNode }) {
  return (
    <div className={styles.frame}>
      <SkipLink href="#auth-main" label="Skip to authentication form" />
      <header className={styles.frameHeader}>
        <Link className={styles.brand} href="/" aria-label="Signal Ledger home">
          <span aria-hidden="true">SL</span>
          <strong>Signal Ledger</strong>
        </Link>
        <ThemeSelector compact />
      </header>
      {children}
      <footer className={styles.frameFooter}>
        <p>Private administration access</p>
        <Link href="/">Return to the public site</Link>
      </footer>
    </div>
  );
}

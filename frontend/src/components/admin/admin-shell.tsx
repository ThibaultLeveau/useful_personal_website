"use client";

import type { Route } from "next";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useRef, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { ThemeSelector } from "@/components/ui/theme-selector";

const navigation = [
  { href: "/admin", label: "Overview", index: "01" },
  { href: "/admin/profile", label: "Profile", index: "02" },
  { href: "/admin/settings", label: "Settings", index: "03" },
  { href: "/admin/navigation", label: "Navigation", index: "04" },
  { href: "/admin/footer", label: "Footer", index: "05" },
  { href: "/admin/skills", label: "Skills", index: "06" },
  { href: "/admin/experiences", label: "Experience", index: "07" },
  { href: "/admin/projects", label: "Projects", index: "08" },
  { href: "/admin/blog", label: "Blog", index: "09" },
  { href: "/admin/pages", label: "Pages", index: "10" },
  { href: "/admin/media", label: "Media", index: "11" },
  { href: "/admin/contacts", label: "Contacts", index: "12" },
  { href: "/admin/api-tokens", label: "API tokens", index: "13" },
  { href: "/admin/audit", label: "Audit", index: "14" },
  { href: "/admin/health", label: "Health", index: "15" },
] as const;

function AdminNavigation({ close }: { close?: () => void }) {
  const pathname = usePathname();

  return (
    <nav className="admin-navigation" aria-label="Administration">
      <p className="admin-navigation__label">Workspace</p>
      {navigation.map((item) => (
        <Link
          aria-current={pathname === item.href ? "page" : undefined}
          href={item.href as Route}
          key={item.href}
          title={item.label}
          {...(close ? { onClick: close } : {})}
        >
          <span aria-hidden="true">{item.index}</span>
          <strong>{item.label}</strong>
        </Link>
      ))}
    </nav>
  );
}

export function AdminShell({ children }: { children: ReactNode }) {
  const menuButton = useRef<HTMLButtonElement>(null);
  const menuDialog = useRef<HTMLDialogElement>(null);

  function closeMenu() {
    menuDialog.current?.close();
  }

  return (
    <div className="admin-shell">
      <aside className="admin-sidebar" aria-label="Administration sidebar">
        <Link className="admin-wordmark" href="/admin" aria-label="Signal Ledger administration">
          <span aria-hidden="true">SL</span>
          <strong>Signal Ledger</strong>
        </Link>
        <AdminNavigation />
        <ThemeSelector compact />
      </aside>

      <div className="admin-workspace">
        <header className="admin-mobile-header">
          <Link href="/admin">Signal Ledger</Link>
          <Button
            aria-haspopup="dialog"
            onClick={() => menuDialog.current?.showModal()}
            ref={menuButton}
            variant="secondary"
          >
            Menu
          </Button>
        </header>
        {children}
      </div>

      <dialog
        aria-labelledby="admin-menu-title"
        className="navigation-dialog"
        onClose={() => menuButton.current?.focus()}
        ref={menuDialog}
      >
        <div className="navigation-dialog__header">
          <h2 id="admin-menu-title">Administration</h2>
          <Button onClick={closeMenu} variant="quiet">
            Close
          </Button>
        </div>
        <AdminNavigation close={closeMenu} />
        <ThemeSelector />
      </dialog>
    </div>
  );
}

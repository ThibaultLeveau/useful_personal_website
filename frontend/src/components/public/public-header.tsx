"use client";

import type { Route } from "next";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef } from "react";

import { Button } from "@/components/ui/button";
import { ThemeSelector } from "@/components/ui/theme-selector";
import { LinkTarget, type PublicNavigationItemData } from "@/generated/api/src/models";

import { ResponsiveMediaImage } from "./responsive-media-image";

function NavigationLink({ item, close }: { item: PublicNavigationItemData; close?: () => void }) {
  const pathname = usePathname();
  const external = item.href.startsWith("https://");
  const newWindow = item.target === LinkTarget.NewWindow;
  const current = !external && pathname === item.href;
  const className = item.parentKey ? "public-nav__child" : undefined;

  if (external) {
    return (
      <a
        className={className}
        href={item.href}
        {...(close ? { onClick: close } : {})}
        {...(newWindow ? { rel: "noopener noreferrer", target: "_blank" } : {})}
      >
        {item.label}
      </a>
    );
  }
  return (
    <Link
      aria-current={current ? "page" : undefined}
      className={className}
      href={item.href as Route}
      {...(close ? { onClick: close } : {})}
    >
      {item.label}
    </Link>
  );
}

export function orderPublicNavigation(
  navigation: readonly PublicNavigationItemData[],
): PublicNavigationItemData[] {
  const roots = navigation.filter((item) => !item.parentKey);
  const placed = new Set(roots.map((item) => item.key));
  const result = roots.flatMap((root) => {
    const children = navigation.filter((item) => item.parentKey === root.key);
    children.forEach((item) => placed.add(item.key));
    return [root, ...children];
  });
  return [...result, ...navigation.filter((item) => !placed.has(item.key))];
}

export function PublicHeader({
  brand,
  logoMediaId,
  navigation,
}: {
  brand?: string | null;
  logoMediaId?: string | null;
  navigation: readonly PublicNavigationItemData[];
}) {
  const menuButton = useRef<HTMLButtonElement>(null);
  const menuDialog = useRef<HTMLDialogElement>(null);
  const previousOverflow = useRef("");
  const orderedNavigation = orderPublicNavigation(navigation);

  function unlockPage() {
    document.documentElement.style.overflow = previousOverflow.current;
  }

  function openMenu() {
    previousOverflow.current = document.documentElement.style.overflow;
    document.documentElement.style.overflow = "hidden";
    menuDialog.current?.showModal();
  }

  function closeMenu() {
    menuDialog.current?.close();
  }

  useEffect(() => unlockPage, []);

  return (
    <header className="public-header">
      <div className="public-header__inner">
        <Link className="wordmark" href="/" aria-label={brand ? `${brand} home` : "Home"}>
          {logoMediaId ? (
            <ResponsiveMediaImage
              alt=""
              assetId={logoMediaId}
              className="wordmark__media"
              eager
              sizes="32px"
            />
          ) : (
            <span aria-hidden="true">{brand ? brand.slice(0, 2).toLocaleUpperCase() : "⌂"}</span>
          )}
          <strong>{brand ?? "Home"}</strong>
        </Link>

        <nav className="public-nav public-nav--desktop" aria-label="Primary navigation">
          {orderedNavigation.map((item) => (
            <NavigationLink item={item} key={item.key} />
          ))}
        </nav>

        <div className="public-header__actions">
          <ThemeSelector compact />
          <Button
            aria-haspopup="dialog"
            className="public-header__menu-button"
            onClick={openMenu}
            ref={menuButton}
            variant="secondary"
          >
            Menu
          </Button>
        </div>
      </div>

      <dialog
        aria-labelledby="public-menu-title"
        className="navigation-dialog"
        onCancel={unlockPage}
        onClose={() => {
          unlockPage();
          menuButton.current?.focus();
        }}
        ref={menuDialog}
      >
        <div className="navigation-dialog__header">
          <h2 id="public-menu-title">Navigation</h2>
          <Button onClick={closeMenu} variant="quiet">
            Close
          </Button>
        </div>
        <nav aria-label="Mobile navigation">
          {orderedNavigation.map((item) => (
            <NavigationLink close={closeMenu} item={item} key={item.key} />
          ))}
        </nav>
        <ThemeSelector />
      </dialog>
    </header>
  );
}

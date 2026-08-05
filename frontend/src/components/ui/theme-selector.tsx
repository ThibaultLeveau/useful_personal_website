"use client";

import { useEffect, useId, useSyncExternalStore } from "react";

type ThemePreference = "dark" | "light" | "system";

const storageKey = "upw-theme";
const darkScheme = "(prefers-color-scheme: dark)";
const preferenceChangeEvent = "upw-theme-change";

function isThemePreference(value: string | null): value is ThemePreference {
  return value === "dark" || value === "light" || value === "system";
}

function applyTheme(preference: ThemePreference) {
  const resolved =
    preference === "system"
      ? window.matchMedia(darkScheme).matches
        ? "dark"
        : "light"
      : preference;

  document.documentElement.dataset.theme = resolved;
  document.documentElement.dataset.themePreference = preference;
  document.documentElement.style.colorScheme = resolved;
}

function getPreference(): ThemePreference {
  const stored = window.localStorage.getItem(storageKey);
  return isThemePreference(stored) ? stored : "system";
}

function subscribeToPreference(onStoreChange: () => void) {
  window.addEventListener("storage", onStoreChange);
  window.addEventListener(preferenceChangeEvent, onStoreChange);
  return () => {
    window.removeEventListener("storage", onStoreChange);
    window.removeEventListener(preferenceChangeEvent, onStoreChange);
  };
}

function subscribeToHydration() {
  return () => undefined;
}

export function ThemeSelector({ compact = false }: { compact?: boolean }) {
  const labelId = useId();
  const hydrated = useSyncExternalStore(
    subscribeToHydration,
    () => true,
    () => false,
  );
  const preference = useSyncExternalStore<ThemePreference>(
    subscribeToPreference,
    getPreference,
    () => "system",
  );

  useEffect(() => {
    applyTheme(preference);
    const media = window.matchMedia(darkScheme);
    const handleSystemChange = () => {
      if (preference === "system") applyTheme("system");
    };
    media.addEventListener("change", handleSystemChange);
    return () => media.removeEventListener("change", handleSystemChange);
  }, [preference]);

  return (
    <label className={compact ? "theme-selector theme-selector--compact" : "theme-selector"}>
      <span id={labelId}>Theme</span>
      <select
        aria-labelledby={labelId}
        disabled={!hydrated}
        value={preference}
        onChange={(event) => {
          const nextPreference = event.target.value;
          if (!isThemePreference(nextPreference)) return;
          applyTheme(nextPreference);
          window.localStorage.setItem(storageKey, nextPreference);
          window.dispatchEvent(new Event(preferenceChangeEvent));
        }}
      >
        <option value="system">System</option>
        <option value="light">Light</option>
        <option value="dark">Dark</option>
      </select>
    </label>
  );
}

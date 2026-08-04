"use client";

import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api";

import styles from "./configuration.module.css";

export function FormStatus({ error, saved }: { error?: ApiError | null; saved?: string | null }) {
  const summary = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (error) summary.current?.focus();
  }, [error]);

  if (error) {
    const conflict = error.code === "RESOURCE_VERSION_CONFLICT";
    return (
      <div className={styles.errorSummary} ref={summary} role="alert" tabIndex={-1}>
        <h2>{conflict ? "This record changed elsewhere" : "The changes were not saved"}</h2>
        <p>
          {conflict
            ? "Your edits are still here. Reload the current version before deciding what to keep."
            : error.message}
        </p>
        {error.requestId ? <p className={styles.requestId}>Request ID: {error.requestId}</p> : null}
      </div>
    );
  }
  return saved ? (
    <p className={styles.successMessage} role="status">
      {saved}
    </p>
  ) : null;
}

export function UnsavedChangesGuard({
  dirty,
  onSave,
}: {
  dirty: boolean;
  onSave: () => Promise<boolean>;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const pendingHref = useRef<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    function beforeUnload(event: BeforeUnloadEvent) {
      if (!dirty) return;
      event.preventDefault();
    }
    function captureNavigation(event: MouseEvent) {
      if (!dirty || event.defaultPrevented || event.button !== 0) return;
      const target = event.target;
      if (!(target instanceof Element)) return;
      const anchor = target.closest("a[href]");
      if (!(anchor instanceof HTMLAnchorElement)) return;
      const destination = new URL(anchor.href, window.location.href);
      if (destination.origin !== window.location.origin) return;
      if (destination.pathname === window.location.pathname) return;
      event.preventDefault();
      pendingHref.current = destination.href;
      dialog.current?.showModal();
    }
    window.addEventListener("beforeunload", beforeUnload);
    document.addEventListener("click", captureNavigation, true);
    return () => {
      window.removeEventListener("beforeunload", beforeUnload);
      document.removeEventListener("click", captureNavigation, true);
    };
  }, [dirty]);

  function continueNavigation() {
    const href = pendingHref.current;
    dialog.current?.close();
    if (href) window.location.assign(href);
  }

  return (
    <>
      <p className={styles.dirtyStatus} role="status">
        {dirty ? "Unsaved changes" : "All changes saved"}
      </p>
      <dialog aria-labelledby="unsaved-title" className={styles.guardDialog} ref={dialog}>
        <h2 id="unsaved-title">Leave with unsaved changes?</h2>
        <p>Your edits have not been saved.</p>
        <div className="button-row">
          <Button onClick={() => dialog.current?.close()} variant="secondary">
            Stay
          </Button>
          <Button onClick={continueNavigation} variant="danger">
            Leave without saving
          </Button>
          <Button
            disabled={saving}
            onClick={() => {
              setSaving(true);
              void onSave().then((saved) => {
                setSaving(false);
                if (saved) continueNavigation();
              });
            }}
          >
            {saving ? "Saving…" : "Save and continue"}
          </Button>
        </div>
      </dialog>
    </>
  );
}

export function toApiError(error: unknown): ApiError {
  return error instanceof ApiError
    ? error
    : new ApiError({
        code: "API_CLIENT_ERROR",
        message: "The request failed safely. Your edits remain in this browser.",
        status: 0,
      });
}

export function splitLines(value: string): string[] {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function optional(value: string): string | null {
  const normalized = value.trim();
  return normalized || null;
}

export function useDeferredInitialLoad(load: () => Promise<void>): void {
  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);
}

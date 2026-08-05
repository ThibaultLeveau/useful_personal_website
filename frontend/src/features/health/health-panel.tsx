"use client";

import type { Route } from "next";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { LoadingPanel } from "@/components/ui/loading-panel";
import type { AdminHealthData } from "@/generated/api/src/models";
import { ApiError, createApiClient, type AdminHealthApiBoundary } from "@/lib/api";

import { useOptionalAuth } from "../auth/auth-context";
import { expiredPathFor } from "../auth/safe-return";
import styles from "./health.module.css";

const defaultApi = createApiClient().adminHealth;

type VisibleStatus = "Operational" | "Degraded" | "Unavailable" | "Unknown";

export interface HealthPanelProps {
  api?: AdminHealthApiBoundary;
}

function visibleStatus(snapshot: AdminHealthData | undefined, error: ApiError | undefined) {
  if (snapshot?.status === "operational") return "Operational" satisfies VisibleStatus;
  if (snapshot?.status === "degraded") return "Degraded" satisfies VisibleStatus;
  if (error?.code === "API_UNAVAILABLE") return "Unavailable" satisfies VisibleStatus;
  return "Unknown" satisfies VisibleStatus;
}

function formatCheckedAt(value: Date) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "medium",
  }).format(value);
}

function safeError(error: unknown): ApiError {
  if (error instanceof ApiError) return error;
  return new ApiError({
    code: "API_CLIENT_ERROR",
    message: "The API request failed safely.",
    status: 0,
  });
}

export function HealthPanel({ api = defaultApi }: HealthPanelProps) {
  const pathname = usePathname();
  const router = useRouter();
  const auth = useOptionalAuth();
  const [snapshot, setSnapshot] = useState<AdminHealthData>();
  const snapshotRef = useRef<AdminHealthData | undefined>(undefined);
  const [error, setError] = useState<ApiError>();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [stale, setStale] = useState(false);
  const [redirecting, setRedirecting] = useState(false);
  const [announcement, setAnnouncement] = useState("");

  const load = useCallback(
    async (signal?: AbortSignal, refresh = false) => {
      if (refresh) {
        setRefreshing(true);
        setAnnouncement("");
      }
      try {
        const response = await api.get(signal ? { signal } : undefined);
        if (signal?.aborted) return;
        snapshotRef.current = response.data;
        setSnapshot(response.data);
        setError(undefined);
        setStale(false);
        if (refresh) {
          setAnnouncement(`Health status refreshed. ${visibleStatus(response.data, undefined)}.`);
        }
      } catch (caught: unknown) {
        if (signal?.aborted) return;
        const nextError = safeError(caught);
        if (nextError.status === 401) {
          snapshotRef.current = undefined;
          setSnapshot(undefined);
          setError(undefined);
          setRedirecting(true);
          if (auth) auth.expireSession();
          else router.replace(expiredPathFor(pathname) as Route);
          return;
        }
        if (nextError.code === "PASSWORD_CHANGE_REQUIRED" || nextError.status === 403) {
          snapshotRef.current = undefined;
          setSnapshot(undefined);
          setError(undefined);
          setRedirecting(true);
          router.replace("/admin/change-password" as Route);
          return;
        }
        setError(nextError);
        setStale(Boolean(snapshotRef.current));
        if (refresh) setAnnouncement("Health refresh failed. The previous result is marked stale.");
      } finally {
        if (!signal?.aborted) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    },
    [api, auth, pathname, router],
  );

  useEffect(() => {
    const controller = new AbortController();
    void Promise.resolve().then(() => load(controller.signal));
    return () => controller.abort();
  }, [load]);

  if (redirecting) {
    return (
      <p aria-live="polite" role="status">
        Protected health details were cleared. Redirecting securely&hellip;
      </p>
    );
  }

  if (loading && !snapshot) {
    return <LoadingPanel label="Checking application and dependency health" />;
  }

  const status = visibleStatus(snapshot, error);
  const unavailable = status === "Unavailable";

  return (
    <section aria-labelledby="health-summary-title" className={styles.panel}>
      <p aria-atomic="true" aria-live="polite" className="visually-hidden" role="status">
        {announcement}
      </p>

      <div className={styles.summary}>
        <div>
          <p className="eyebrow">Current assessment</p>
          <h2 id="health-summary-title">System status</h2>
          <p className={styles.explanation}>
            {status === "Operational"
              ? "The application, database, and migration revision are responding normally."
              : status === "Degraded"
                ? "The application is available, but a required dependency needs attention."
                : unavailable
                  ? "The health service could not be reached. Check the connection and try again."
                  : "The latest system state could not be confirmed. Review the guidance and retry."}
          </p>
        </div>
        <p className={styles.status} data-state={status.toLowerCase()}>
          <span aria-hidden="true" className={styles.statusMarker} />
          {status}
        </p>
      </div>

      {snapshot ? (
        <>
          <dl className={styles.metrics}>
            <div>
              <dt>Application</dt>
              <dd>Operational</dd>
            </div>
            <div>
              <dt>Database</dt>
              <dd>{snapshot.databaseStatus === "operational" ? "Operational" : "Unavailable"}</dd>
            </div>
            <div>
              <dt>Migration</dt>
              <dd>
                {snapshot.migrationStatus === "current"
                  ? "Current"
                  : snapshot.migrationStatus === "unavailable"
                    ? "Unavailable"
                    : "Unknown"}
              </dd>
            </div>
          </dl>
          <div className={styles.build}>
            <div>
              <span>Last checked</span>
              <time dateTime={snapshot.checkedAt.toISOString()}>
                {formatCheckedAt(snapshot.checkedAt)}
              </time>
              {stale ? <strong className={styles.stale}>Stale result</strong> : null}
            </div>
            <div>
              <span>Build</span>
              <code>{snapshot.buildVersion}</code>
            </div>
            <div>
              <span>Commit</span>
              <code>{snapshot.buildCommit}</code>
            </div>
          </div>
        </>
      ) : null}

      {error ? (
        <aside className={styles.guidance} aria-labelledby="health-guidance-title">
          <h3 id="health-guidance-title">Recovery guidance</h3>
          <p>
            Confirm network access, then retry. If the problem continues, use the request ID when
            contacting the operator and consult the API health documentation.
          </p>
          {error.requestId ? (
            <p className={styles.requestId}>Request ID: {error.requestId}</p>
          ) : null}
          <Link href={"/api/v1/docs" as Route}>Open API documentation</Link>
        </aside>
      ) : null}

      <div className="button-row">
        <Button disabled={refreshing} onClick={() => void load(undefined, true)}>
          {refreshing ? "Refreshing…" : "Refresh status"}
        </Button>
        <Link className={styles.secondaryAction} href="/admin/account">
          Review account
        </Link>
      </div>
    </section>
  );
}

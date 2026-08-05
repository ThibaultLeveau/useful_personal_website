"use client";

import type { Route } from "next";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { LoadingPanel } from "@/components/ui/loading-panel";
import type { ActorType, AuditEntryData, AuditOutcome } from "@/generated/api/src/models";
import { ApiError } from "@/lib/api";

import { useOptionalAuth } from "../auth/auth-context";
import { expiredPathFor } from "../auth/safe-return";
import { auditApi, type AuditApi, type AuditFilters } from "./api";
import styles from "./audit.module.css";

const EMPTY_FILTERS: AuditFilters = { page: 1 };

function formatTime(value: Date) {
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "medium" }).format(
    value,
  );
}

function actor(entry: AuditEntryData) {
  return entry.actorLabel ?? entry.actorType.replaceAll("_", " ");
}

function resource(entry: AuditEntryData) {
  if (!entry.resourceType) return "—";
  return entry.resourceId
    ? `${entry.resourceType} · ${entry.resourceId.slice(0, 8)}…`
    : entry.resourceType;
}

function dateValue(value: FormDataEntryValue | null): Date | undefined {
  if (typeof value !== "string" || value === "") return undefined;
  const parsed = new Date(value);
  return Number.isFinite(parsed.getTime()) ? parsed : undefined;
}

function textValue(value: FormDataEntryValue | null) {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

export function AuditViewer({ api = auditApi }: { api?: AuditApi }) {
  const pathname = usePathname();
  const router = useRouter();
  const auth = useOptionalAuth();
  const [filters, setFilters] = useState<AuditFilters>(EMPTY_FILTERS);
  const [events, setEvents] = useState<string[]>([]);
  const [entries, setEntries] = useState<AuditEntryData[]>([]);
  const [totalPages, setTotalPages] = useState(0);
  const [totalItems, setTotalItems] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [redirecting, setRedirecting] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    void Promise.all([api.events(controller.signal), api.list(filters, controller.signal)])
      .then(([catalog, result]) => {
        if (controller.signal.aborted) return;
        setEvents(catalog);
        setEntries(result.data);
        setTotalPages(result.meta.pagination.totalPages);
        setTotalItems(result.meta.pagination.totalItems);
      })
      .catch((caught: unknown) => {
        if (controller.signal.aborted) return;
        if (caught instanceof ApiError && caught.status === 401) {
          setEntries([]);
          setRedirecting(true);
          if (auth) auth.expireSession();
          else router.replace(expiredPathFor(pathname) as Route);
          return;
        }
        setError("The audit record could not be loaded safely. Try again.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [api, auth, filters, pathname, router]);

  const chips = useMemo(
    () =>
      Object.entries(filters).filter(
        ([key, value]) => key !== "page" && value !== undefined && value !== "",
      ),
    [filters],
  );

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const eventType = textValue(data.get("eventType"));
    const actorType = textValue(data.get("actorType"));
    const outcome = textValue(data.get("outcome"));
    const actorId = textValue(data.get("actorId"));
    const resourceType = textValue(data.get("resourceType"));
    const resourceId = textValue(data.get("resourceId"));
    const requestId = textValue(data.get("requestId"));
    const occurredFrom = dateValue(data.get("occurredFrom"));
    const occurredTo = dateValue(data.get("occurredTo"));
    setLoading(true);
    setError("");
    setFilters({
      page: 1,
      ...(eventType ? { eventType } : {}),
      ...(actorType ? { actorType: actorType as ActorType } : {}),
      ...(outcome ? { outcome: outcome as AuditOutcome } : {}),
      ...(actorId ? { actorId } : {}),
      ...(resourceType ? { resourceType } : {}),
      ...(resourceId ? { resourceId } : {}),
      ...(requestId ? { requestId } : {}),
      ...(occurredFrom ? { occurredFrom } : {}),
      ...(occurredTo ? { occurredTo } : {}),
    });
  }

  function removeFilter(key: string) {
    setLoading(true);
    setError("");
    setFilters((current) => ({ ...current, [key]: undefined, page: 1 }));
  }

  function clearFilters() {
    setLoading(true);
    setError("");
    setFilters(EMPTY_FILTERS);
  }

  function changePage(page: number) {
    setLoading(true);
    setError("");
    setFilters((value) => ({ ...value, page }));
  }

  if (redirecting) {
    return <p role="status">Protected audit details were cleared. Redirecting securely…</p>;
  }

  return (
    <section aria-labelledby="audit-title" className={styles.viewer}>
      <header className={styles.intro}>
        <div>
          <p className="eyebrow">Security record</p>
          <h1 id="audit-title">Audit activity</h1>
          <p>Inspect allow-listed operational facts. Sensitive payloads are never stored here.</p>
        </div>
        <p aria-live="polite" className={styles.count} role="status">
          {totalItems} {totalItems === 1 ? "event" : "events"}
        </p>
      </header>

      <form className={styles.filters} onSubmit={submit}>
        <label>
          Event
          <select defaultValue="" name="eventType">
            <option value="">All events</option>
            {events.map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </label>
        <label>
          Actor
          <select defaultValue="" name="actorType">
            <option value="">All actors</option>
            <option value="administrator">Administrator</option>
            <option value="anonymous">Anonymous</option>
            <option value="system">System</option>
          </select>
        </label>
        <label>
          Outcome
          <select defaultValue="" name="outcome">
            <option value="">All outcomes</option>
            <option value="success">Success</option>
            <option value="failure">Failure</option>
            <option value="denied">Denied</option>
          </select>
        </label>
        <label>
          Resource type
          <input maxLength={80} name="resourceType" placeholder="project" />
        </label>
        <label>
          Exact actor ID
          <input name="actorId" placeholder="UUID" />
        </label>
        <label>
          Exact resource ID
          <input name="resourceId" placeholder="UUID" />
        </label>
        <label>
          From (UTC)
          <input name="occurredFrom" type="datetime-local" />
        </label>
        <label>
          To (UTC)
          <input name="occurredTo" type="datetime-local" />
        </label>
        <label className={styles.requestFilter}>
          Exact request ID
          <input maxLength={128} name="requestId" />
        </label>
        <div className={styles.filterActions}>
          <Button type="submit">Apply filters</Button>
          <Button onClick={clearFilters} type="reset" variant="secondary">
            Clear
          </Button>
        </div>
      </form>

      {chips.length ? (
        <div aria-label="Active filters" className={styles.chips}>
          {chips.map(([key, value]) => (
            <button key={key} onClick={() => removeFilter(key)} type="button">
              {key}: {value instanceof Date ? value.toISOString() : String(value)}{" "}
              <span aria-hidden="true">×</span>
              <span className="visually-hidden"> Remove filter</span>
            </button>
          ))}
        </div>
      ) : null}

      {loading ? <LoadingPanel label="Loading protected audit activity" /> : null}
      {error ? <p role="alert">{error}</p> : null}
      {!loading && !error && entries.length === 0 ? (
        <div className={styles.empty}>
          <h2>No matching events</h2>
          <p>Remove a filter or check again after an administrative action.</p>
        </div>
      ) : null}
      {!loading && !error && entries.length ? (
        <>
          <div
            className={styles.tableWrap}
            tabIndex={0}
            role="region"
            aria-label="Audit events; scroll horizontally if needed"
          >
            <table className={styles.table}>
              <thead>
                <tr>
                  <th scope="col">When</th>
                  <th scope="col">Event</th>
                  <th scope="col">Actor</th>
                  <th scope="col">Resource</th>
                  <th scope="col">Outcome</th>
                  <th scope="col">
                    <span className="visually-hidden">Details</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry) => (
                  <tr key={entry.id}>
                    <td>
                      <time dateTime={entry.occurredAt.toISOString()}>
                        {formatTime(entry.occurredAt)}
                      </time>
                    </td>
                    <td>
                      <code>{entry.eventType}</code>
                    </td>
                    <td>{actor(entry)}</td>
                    <td>{resource(entry)}</td>
                    <td>
                      <span className={styles.outcome} data-outcome={entry.outcome}>
                        {entry.outcome}
                      </span>
                    </td>
                    <td>
                      <Link href={`/admin/audit/${entry.id}` as Route}>View</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <ul className={styles.cards} aria-label="Audit events">
            {entries.map((entry) => (
              <li key={entry.id}>
                <div>
                  <code>{entry.eventType}</code>
                  <span className={styles.outcome} data-outcome={entry.outcome}>
                    {entry.outcome}
                  </span>
                </div>
                <time dateTime={entry.occurredAt.toISOString()}>
                  {formatTime(entry.occurredAt)}
                </time>
                <dl>
                  <div>
                    <dt>Actor</dt>
                    <dd>{actor(entry)}</dd>
                  </div>
                  <div>
                    <dt>Resource</dt>
                    <dd>{resource(entry)}</dd>
                  </div>
                </dl>
                <Link href={`/admin/audit/${entry.id}` as Route}>View event details</Link>
              </li>
            ))}
          </ul>
          <nav aria-label="Audit pagination" className={styles.pagination}>
            <Button
              disabled={filters.page <= 1}
              onClick={() => changePage(filters.page - 1)}
              variant="secondary"
            >
              Previous
            </Button>
            <span>
              Page {filters.page} of {Math.max(totalPages, 1)}
            </span>
            <Button
              disabled={filters.page >= totalPages}
              onClick={() => changePage(filters.page + 1)}
              variant="secondary"
            >
              Next
            </Button>
          </nav>
        </>
      ) : null}
    </section>
  );
}

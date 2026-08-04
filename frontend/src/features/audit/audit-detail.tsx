"use client";

import type { Route } from "next";
import Link from "next/link";
import { useEffect, useState } from "react";

import { LoadingPanel } from "@/components/ui/loading-panel";
import type { AuditEntryData } from "@/generated/api/src/models";

import { auditApi, type AuditApi } from "./api";
import styles from "./audit.module.css";

export function AuditDetail({ id, api = auditApi }: { id: string; api?: AuditApi }) {
  const [entry, setEntry] = useState<AuditEntryData>();
  const [error, setError] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    void api
      .get(id, controller.signal)
      .then(setEntry)
      .catch(() => setError(true));
    return () => controller.abort();
  }, [api, id]);
  if (error) return <p role="alert">This audit event could not be loaded safely.</p>;
  if (!entry) return <LoadingPanel label="Loading protected audit event" />;
  return (
    <article className={styles.detail}>
      <Link href={"/admin/audit" as Route}>← Back to audit activity</Link>
      <header>
        <p className="eyebrow">Audit event</p>
        <h1>{entry.eventType}</h1>
        <span className={styles.outcome} data-outcome={entry.outcome}>
          {entry.outcome}
        </span>
      </header>
      <dl>
        <div>
          <dt>Occurred</dt>
          <dd>
            <time dateTime={entry.occurredAt.toISOString()}>
              {entry.occurredAt.toLocaleString()}
            </time>
          </dd>
        </div>
        <div>
          <dt>Actor type</dt>
          <dd>{entry.actorType}</dd>
        </div>
        <div>
          <dt>Actor identifier</dt>
          <dd>
            <code>{entry.actorId ?? "Not recorded"}</code>
          </dd>
        </div>
        <div>
          <dt>Resource</dt>
          <dd>
            <code>
              {entry.resourceType ?? "Not recorded"}
              {entry.resourceId ? ` · ${entry.resourceId}` : ""}
            </code>
          </dd>
        </div>
        <div>
          <dt>Request ID</dt>
          <dd>
            <code>{entry.requestId}</code>
          </dd>
        </div>
        <div>
          <dt>Schema version</dt>
          <dd>{entry.schemaVersion}</dd>
        </div>
      </dl>
      <section aria-labelledby="audit-metadata">
        <h2 id="audit-metadata">Safe metadata</h2>
        <p>
          Only event-specific allow-listed facts are retained. Sensitive values are absent, not
          masked.
        </p>
        {Object.keys(entry.metadata).length ? (
          <dl>
            {Object.entries(entry.metadata).map(([key, value]) => (
              <div key={key}>
                <dt>{key.replaceAll("_", " ")}</dt>
                <dd>
                  <code>{value}</code>
                </dd>
              </div>
            ))}
          </dl>
        ) : (
          <p>No metadata was recorded for this event.</p>
        )}
      </section>
    </article>
  );
}

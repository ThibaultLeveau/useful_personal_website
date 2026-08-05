"use client";

import type { Route } from "next";
import Link from "next/link";
import { useCallback, useState } from "react";

import { Button } from "@/components/ui/button";
import { LoadingPanel } from "@/components/ui/loading-panel";
import type { AdminExperiencesListRequest } from "@/generated/api/src/apis/ExperiencesApi";
import type {
  ExperienceCreateRequest,
  ExperienceData,
  PaginationData,
} from "@/generated/api/src/models";
import { useAuth } from "@/features/auth/auth-context";
import {
  FormStatus,
  toApiError,
  useDeferredInitialLoad,
} from "@/features/site-configuration/configuration-form";
import { ApiError } from "@/lib/api";

import { adminExperiencesApi, type AdminExperiencesApiBoundary } from "./admin-api";
import styles from "./experiences-admin.module.css";

const lifecycleLabels: Record<ExperienceData["lifecycle"], string> = {
  deleted: "Deleted",
  draft: "Draft",
  published: "Published",
  published_changes_pending: "Published — changes pending",
  scheduled: "Scheduled",
  unpublished: "Unpublished",
};

function move<Item>(items: Item[], index: number, direction: -1 | 1): Item[] {
  const target = index + direction;
  if (target < 0 || target >= items.length) return items;
  const next = [...items];
  [next[index], next[target]] = [next[target] as Item, next[index] as Item];
  return next;
}

function dateInput(value: FormDataEntryValue | null): Date {
  return new Date(`${String(value)}T00:00:00.000Z`);
}

export function ExperienceManager({
  api = adminExperiencesApi,
}: {
  api?: AdminExperiencesApiBoundary;
}) {
  const auth = useAuth();
  const [items, setItems] = useState<ExperienceData[]>([]);
  const [pagination, setPagination] = useState<PaginationData | null>(null);
  const [filters, setFilters] = useState<AdminExperiencesListRequest>({});
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [saved, setSaved] = useState<string | null>(null);

  const load = useCallback(
    async (nextFilters: AdminExperiencesListRequest = {}) => {
      setLoading(true);
      setError(null);
      try {
        const snapshot = await api.list(nextFilters);
        setItems(snapshot.items);
        setPagination(snapshot.pagination);
        setFilters(nextFilters);
      } catch (caught) {
        const next = toApiError(caught);
        setError(next);
        if (next.status === 401) auth.expireSession();
      } finally {
        setLoading(false);
      }
    },
    [api, auth],
  );

  useDeferredInitialLoad(load);

  async function mutate(action: () => Promise<void>, message: string): Promise<void> {
    setBusy(true);
    setError(null);
    setSaved(null);
    try {
      await action();
      setSaved(message);
    } catch (caught) {
      const next = toApiError(caught);
      setError(next);
      if (next.status === 401) auth.expireSession();
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <LoadingPanel label="Loading experience workspace" />;

  const completeOrder =
    !filters.lifecycle &&
    filters.visible === undefined &&
    filters.current === undefined &&
    !filters.search &&
    (filters.page ?? 1) === 1 &&
    pagination?.totalItems === items.length;

  return (
    <>
      <header className={styles.pageHeader}>
        <div>
          <p className="eyebrow">Content / Experience</p>
          <h1>Experience ledger</h1>
          <p>Shape drafts, review private previews, and control each publication independently.</p>
        </div>
        <Button onClick={() => void load(filters)} variant="secondary">
          Refresh
        </Button>
      </header>
      <FormStatus error={error} saved={saved} />
      {error?.code === "RESOURCE_VERSION_CONFLICT" ? (
        <Button onClick={() => void load(filters)} variant="secondary">
          Review latest versions
        </Button>
      ) : null}

      <section className={styles.panel} aria-labelledby="new-experience-title">
        <header className={styles.panelHeader}>
          <div>
            <p className="eyebrow">New draft</p>
            <h2 id="new-experience-title">Start with the essentials</h2>
          </div>
        </header>
        <form
          className={styles.createForm}
          onSubmit={(event) => {
            event.preventDefault();
            const form = event.currentTarget;
            const data = new FormData(form);
            const input: ExperienceCreateRequest = {
              achievements: [],
              companyName: String(data.get("companyName") ?? "").trim(),
              companyUrl: null,
              currentPosition: true,
              detailedDescription: null,
              employmentType: "full_time",
              endDate: null,
              location: null,
              remoteStatus: "hybrid",
              responsibilities: [],
              roleTitle: String(data.get("roleTitle") ?? "").trim(),
              shortSummary: String(data.get("shortSummary") ?? "").trim(),
              skillIds: [],
              startDate: dateInput(data.get("startDate")),
              technologies: [],
              visible: true,
            };
            void mutate(async () => {
              const created = await api.create(input);
              window.location.assign(`/admin/experiences/${created.id}/edit`);
            }, "Draft created.");
          }}
        >
          <label>
            Company
            <input maxLength={160} name="companyName" required />
          </label>
          <label>
            Role title
            <input maxLength={160} name="roleTitle" required />
          </label>
          <label>
            Start date
            <input name="startDate" required type="date" />
          </label>
          <label className={styles.wide}>
            Short summary
            <textarea maxLength={500} name="shortSummary" required rows={2} />
          </label>
          <Button disabled={busy} type="submit">
            {busy ? "Creating…" : "Create draft"}
          </Button>
        </form>
      </section>

      <section className={styles.panel} aria-labelledby="experience-list-title">
        <header className={styles.panelHeader}>
          <div>
            <p className="eyebrow">Records</p>
            <h2 id="experience-list-title">All experiences</h2>
          </div>
          <span>{pagination?.totalItems ?? 0} total</span>
        </header>
        <form
          className={styles.filters}
          onSubmit={(event) => {
            event.preventDefault();
            const data = new FormData(event.currentTarget);
            const lifecycle = String(data.get("lifecycle") ?? "");
            const visible = String(data.get("visible") ?? "");
            const search = String(data.get("search") ?? "").trim();
            void load({
              ...(lifecycle ? { lifecycle: lifecycle as ExperienceData["lifecycle"] } : {}),
              ...(search ? { search } : {}),
              ...(visible ? { visible: visible === "true" } : {}),
            });
          }}
        >
          <label>
            Search
            <input defaultValue={filters.search} maxLength={120} name="search" type="search" />
          </label>
          <label>
            Lifecycle
            <select defaultValue={filters.lifecycle ?? ""} name="lifecycle">
              <option value="">All states</option>
              {Object.entries(lifecycleLabels).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Visibility
            <select
              defaultValue={filters.visible === undefined ? "" : String(filters.visible)}
              name="visible"
            >
              <option value="">Any visibility</option>
              <option value="true">Visible</option>
              <option value="false">Hidden</option>
            </select>
          </label>
          <Button disabled={busy} type="submit">
            Apply filters
          </Button>
        </form>

        {items.length ? (
          <ol className={styles.recordList}>
            {items.map((item, index) => (
              <li className={styles.record} key={item.id}>
                <div className={styles.recordMain}>
                  <div>
                    <p className={styles.position}>Position {item.position + 1}</p>
                    <h3>{item.draft.roleTitle}</h3>
                    <p>{item.draft.companyName}</p>
                  </div>
                  <div className={styles.statusCluster}>
                    <span className={styles.status} data-state={item.lifecycle}>
                      <i aria-hidden="true" /> {lifecycleLabels[item.lifecycle]}
                    </span>
                    <span className={styles.visibility}>
                      {item.visible ? "◆ Visible" : "◇ Hidden"}
                    </span>
                  </div>
                </div>
                <div className={styles.recordActions}>
                  <Link
                    className="button button--secondary"
                    href={`/admin/experiences/${item.id}/edit` as Route}
                  >
                    Edit
                  </Link>
                  <Link
                    className="button button--quiet"
                    href={`/admin/experiences/${item.id}/preview` as Route}
                  >
                    Preview draft
                  </Link>
                  <Button
                    disabled={busy}
                    onClick={() =>
                      void mutate(
                        async () => {
                          await api.setVisibility(item, !item.visible);
                          await load(filters);
                        },
                        item.visible ? "Experience hidden." : "Experience visible.",
                      )
                    }
                    variant="quiet"
                  >
                    {item.visible ? "Hide" : "Show"}
                  </Button>
                  <Button
                    aria-label={`Move ${item.draft.roleTitle} earlier`}
                    disabled={busy || !completeOrder || index === 0}
                    onClick={() =>
                      void mutate(async () => {
                        await api.reorder(move(items, index, -1));
                        await load(filters);
                      }, "Order saved.")
                    }
                    variant="quiet"
                  >
                    ↑
                  </Button>
                  <Button
                    aria-label={`Move ${item.draft.roleTitle} later`}
                    disabled={busy || !completeOrder || index === items.length - 1}
                    onClick={() =>
                      void mutate(async () => {
                        await api.reorder(move(items, index, 1));
                        await load(filters);
                      }, "Order saved.")
                    }
                    variant="quiet"
                  >
                    ↓
                  </Button>
                  {item.published ? (
                    <Button
                      disabled={busy}
                      onClick={() => {
                        if (!window.confirm("Unpublish this experience now?")) return;
                        void mutate(async () => {
                          await api.unpublish(item);
                          await load(filters);
                        }, "Experience unpublished.");
                      }}
                      variant="secondary"
                    >
                      Unpublish
                    </Button>
                  ) : null}
                  <Button
                    disabled={busy}
                    onClick={() => {
                      if (
                        !window.confirm("Delete this experience? Revision history is retained.")
                      ) {
                        return;
                      }
                      void mutate(async () => {
                        await api.delete(item);
                        await load(filters);
                      }, "Experience deleted.");
                    }}
                    variant="danger"
                  >
                    Delete
                  </Button>
                </div>
              </li>
            ))}
          </ol>
        ) : (
          <div className={styles.empty} role="status">
            <h3>No experiences found</h3>
            <p>Create the first draft or clear the active filters.</p>
          </div>
        )}

        {pagination ? (
          <nav className={styles.pagination} aria-label="Experience pages">
            <Button
              disabled={busy || !pagination.hasPrevious}
              onClick={() => void load({ ...filters, page: Math.max(1, pagination.page - 1) })}
              variant="secondary"
            >
              Previous
            </Button>
            <span>
              Page {pagination.page} of {Math.max(1, pagination.totalPages)} ·{" "}
              {pagination.totalItems} experiences
            </span>
            <Button
              disabled={busy || !pagination.hasNext}
              onClick={() => void load({ ...filters, page: pagination.page + 1 })}
              variant="secondary"
            >
              Next
            </Button>
          </nav>
        ) : null}
      </section>
    </>
  );
}

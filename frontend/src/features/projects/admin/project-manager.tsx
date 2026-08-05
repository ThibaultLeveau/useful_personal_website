"use client";

import type { Route } from "next";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

import type { ProjectData } from "@/generated/api/src/models";
import { ApiError } from "@/lib/api";

import { adminProjectsApi, type AdminProjectsApiBoundary } from "./admin-api";
import styles from "./projects-admin.module.css";

export function ProjectManager({ api = adminProjectsApi }: { api?: AdminProjectsApiBoundary }) {
  const [items, setItems] = useState<ProjectData[]>([]);
  const [draftSearch, setDraftSearch] = useState("");
  const [draftLifecycle, setDraftLifecycle] = useState("");
  const [filters, setFilters] = useState({ lifecycle: "", search: "" });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const focusResults = useRef(false);
  const resultsHeading = useRef<HTMLHeadingElement>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.list({
        ...(filters.search ? { search: filters.search } : {}),
        ...(filters.lifecycle ? { lifecycle: filters.lifecycle as never } : {}),
      });
      setItems(result.items);
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Projects could not be loaded.");
    } finally {
      setLoading(false);
      if (focusResults.current) {
        focusResults.current = false;
        window.setTimeout(() => resultsHeading.current?.focus(), 0);
      }
    }
  }, [api, filters]);
  useEffect(() => {
    const handle = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(handle);
  }, [load]);

  async function move(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= items.length) return;
    const next = [...items];
    [next[index], next[target]] = [next[target] as ProjectData, next[index] as ProjectData];
    setItems(next);
    try {
      await api.reorder(next);
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "The order could not be saved.");
      void load();
    }
  }
  return (
    <div className={styles.manager}>
      <header className={styles.pageHeader}>
        <div>
          <p className="eyebrow">Content / Projects</p>
          <h1>Project case studies</h1>
          <p>Shape the story, connect evidence, and control each publication independently.</p>
        </div>
        <Link className="button button--primary" href={"/admin/projects/new" as Route}>
          New project
        </Link>
      </header>
      <form
        className={styles.toolbar}
        onSubmit={(event) => {
          event.preventDefault();
          focusResults.current = true;
          setFilters({ lifecycle: draftLifecycle, search: draftSearch.trim() });
        }}
      >
        <label>
          Search
          <input
            onChange={(event) => setDraftSearch(event.target.value)}
            placeholder="Name, summary, or slug"
            value={draftSearch}
          />
        </label>
        <label>
          Lifecycle
          <select
            onChange={(event) => setDraftLifecycle(event.target.value)}
            value={draftLifecycle}
          >
            <option value="">All lifecycle states</option>
            {[
              "draft",
              "scheduled",
              "published",
              "published_changes_pending",
              "unpublished",
              "deleted",
            ].map((value) => (
              <option key={value} value={value}>
                {value.replaceAll("_", " ")}
              </option>
            ))}
          </select>
        </label>
        <button className="button button--secondary" type="submit">
          Apply
        </button>
        <button
          className="button button--quiet"
          onClick={() => {
            setDraftSearch("");
            setDraftLifecycle("");
            focusResults.current = true;
            setFilters({ lifecycle: "", search: "" });
          }}
          type="button"
        >
          Clear
        </button>
      </form>
      <p className={styles.activeFilters} aria-live="polite">
        {filters.search || filters.lifecycle
          ? `Active filters: ${[
              filters.search ? `search “${filters.search}”` : "",
              filters.lifecycle ? `lifecycle ${filters.lifecycle.replaceAll("_", " ")}` : "",
            ]
              .filter(Boolean)
              .join(", ")}`
          : "Showing all project lifecycle states."}
      </p>
      {error ? (
        <div className={styles.error} role="alert">
          <strong>Projects need attention</strong>
          <p>{error}</p>
          <button className="button button--quiet" onClick={() => void load()} type="button">
            Try again
          </button>
        </div>
      ) : null}
      {loading ? (
        <section className={styles.state} role="status">
          Loading project workspace…
        </section>
      ) : items.length ? (
        <>
          <h2 className={styles.resultsHeading} ref={resultsHeading} tabIndex={-1}>
            Project results
          </h2>
          <p className={styles.count}>
            {items.length} project{items.length === 1 ? "" : "s"}
          </p>
          <div className={styles.tableWrap}>
            <table>
              <thead>
                <tr>
                  <th scope="col">Order</th>
                  <th scope="col">Project</th>
                  <th scope="col">Lifecycle</th>
                  <th scope="col">Display</th>
                  <th scope="col">Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item, index) => (
                  <tr key={item.id}>
                    <td>
                      <div className={styles.order}>
                        <button
                          aria-label={`Move ${item.draft.name} up`}
                          disabled={index === 0}
                          onClick={() => void move(index, -1)}
                          type="button"
                        >
                          ↑
                        </button>
                        <span>{index + 1}</span>
                        <button
                          aria-label={`Move ${item.draft.name} down`}
                          disabled={index === items.length - 1}
                          onClick={() => void move(index, 1)}
                          type="button"
                        >
                          ↓
                        </button>
                      </div>
                    </td>
                    <th scope="row">
                      <strong>{item.draft.name}</strong>
                      <small>/{item.slug}</small>
                    </th>
                    <td>
                      <span className={styles.pill}>{item.lifecycle.replaceAll("_", " ")}</span>
                      <small>{item.draft.status}</small>
                    </td>
                    <td>
                      <span>{item.visible ? "Visible" : "Hidden"}</span>
                      <small>{item.featured ? "Featured" : "Standard"}</small>
                    </td>
                    <td>
                      <div className={styles.rowActions}>
                        <Link href={`/admin/projects/${item.id}/edit` as Route}>Edit</Link>
                        <Link href={`/admin/projects/${item.id}/preview` as Route}>Preview</Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className={styles.cards}>
            {items.map((item, index) => (
              <article key={item.id}>
                <p className="eyebrow">
                  {String(index + 1).padStart(2, "0")} · {item.lifecycle.replaceAll("_", " ")}
                </p>
                <h2>{item.draft.name}</h2>
                <p>{item.draft.shortDescription}</p>
                <dl>
                  <div>
                    <dt>Visibility</dt>
                    <dd>{item.visible ? "Visible" : "Hidden"}</dd>
                  </div>
                  <div>
                    <dt>Placement</dt>
                    <dd>{item.featured ? "Featured" : "Standard"}</dd>
                  </div>
                </dl>
                <div className={styles.rowActions}>
                  <Link href={`/admin/projects/${item.id}/edit` as Route}>Edit</Link>
                  <Link href={`/admin/projects/${item.id}/preview` as Route}>Preview</Link>
                </div>
              </article>
            ))}
          </div>
        </>
      ) : (
        <section className={styles.state} role="status">
          <h2>No projects yet.</h2>
          <p>Create the first case study or change the active filters.</p>
          <Link className="button button--primary" href={"/admin/projects/new" as Route}>
            Create project
          </Link>
        </section>
      )}
    </div>
  );
}

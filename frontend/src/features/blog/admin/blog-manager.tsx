"use client";

import type { Route } from "next";
import Link from "next/link";
import { useEffect, useMemo, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { AdminBlogPostsListLifecycleEnum } from "@/generated/api/src/apis/BlogAdministrationApi";
import { TaxonomyKind, type PostData, type TaxonomyData } from "@/generated/api/src/models";
import { ApiError } from "@/lib/api";

import { adminBlogApi, type AdminBlogApiBoundary } from "./admin-api";
import styles from "./blog-admin.module.css";

const date = new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short" });
const message = (error: unknown) =>
  error instanceof ApiError ? error.message : "The request could not be completed.";
const slugify = (value: string) =>
  value
    .normalize("NFKD")
    .toLowerCase()
    .replace(/[^a-z0-9]+/gu, "-")
    .replace(/^-|-$/gu, "");

export function BlogManager({ api = adminBlogApi }: { api?: AdminBlogApiBoundary }) {
  const [items, setItems] = useState<PostData[]>([]);
  const [tags, setTags] = useState<TaxonomyData[]>([]);
  const [categories, setCategories] = useState<TaxonomyData[]>([]);
  const [search, setSearch] = useState("");
  const [lifecycle, setLifecycle] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const filters = {
        ...(search ? { search } : {}),
        ...(lifecycle ? { lifecycle: lifecycle as never } : {}),
      };
      const [result, refs] = await Promise.all([api.list(filters), api.references()]);
      setItems(result.items);
      setTags(refs.tags);
      setCategories(refs.categories);
    } catch (value) {
      setError(message(value));
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    const handle = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(handle);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function createTaxonomy(
    event: FormEvent<HTMLFormElement>,
    kind: typeof TaxonomyKind.Tag | typeof TaxonomyKind.Category,
  ) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const name = String(form.get("name") ?? "").trim();
    if (!name) return;
    try {
      await api.createTaxonomy({ kind, name, slug: slugify(name), visible: true });
      event.currentTarget.reset();
      await load();
    } catch (value) {
      setError(message(value));
    }
  }
  async function removeTaxonomy(item: TaxonomyData) {
    if (!window.confirm(`Delete ${item.name}? In-use taxonomies cannot be deleted.`)) return;
    try {
      await api.deleteTaxonomy(item);
      await load();
    } catch (value) {
      setError(message(value));
    }
  }

  const taxonomyGroups = useMemo(
    () =>
      [
        { title: "Tags", kind: TaxonomyKind.Tag, items: tags },
        { title: "Categories", kind: TaxonomyKind.Category, items: categories },
      ] as const,
    [tags, categories],
  );
  return (
    <div className={styles.manager}>
      <header className={styles.pageHeader}>
        <div>
          <p className="eyebrow">Publishing desk</p>
          <h1>Blog</h1>
          <p>Draft, review, schedule, and publish controlled CommonMark articles.</p>
        </div>
        <Link className="button button--primary" href={"/admin/blog/new" as Route}>
          New article
        </Link>
      </header>
      <form
        className={styles.toolbar}
        onSubmit={(event) => {
          event.preventDefault();
          void load();
        }}
      >
        <label>
          Search
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Title or excerpt"
          />
        </label>
        <label>
          Lifecycle
          <select value={lifecycle} onChange={(event) => setLifecycle(event.target.value)}>
            <option value="">All states</option>
            {Object.entries(AdminBlogPostsListLifecycleEnum).map(([label, value]) => (
              <option key={value} value={value}>
                {label.replaceAll(/([A-Z])/gu, " $1")}
              </option>
            ))}
          </select>
        </label>
        <Button type="submit" disabled={loading}>
          Apply
        </Button>
      </form>
      {error ? (
        <p className={styles.error} role="alert">
          {error}
        </p>
      ) : null}
      {loading ? (
        <p className={styles.state}>Loading the publishing desk…</p>
      ) : items.length ? (
        <div className={styles.tableWrap}>
          <table>
            <thead>
              <tr>
                <th>Article</th>
                <th>State</th>
                <th>Visibility</th>
                <th>Last changed</th>
                <th>
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>
                    <strong>{item.draft.title}</strong>
                    <small>
                      /{item.slug} · rev {item.draft.revisionNumber} · {item.draft.readingMinutes}{" "}
                      min
                    </small>
                  </td>
                  <td>
                    <span className={styles.pill}>{item.lifecycle.replaceAll("_", " ")}</span>
                    {item.publishAt ? <small>{date.format(item.publishAt)}</small> : null}
                  </td>
                  <td>{item.visible ? "Public when published" : "Hidden"}</td>
                  <td>{date.format(item.updatedAt)}</td>
                  <td>
                    <Link href={`/admin/blog/${item.id}/edit` as Route}>Edit</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <section className={styles.state}>
          <h2>No articles yet</h2>
          <p>Create the first draft to begin the archive.</p>
        </section>
      )}
      <section className={styles.taxonomyManager}>
        <div>
          <p className="eyebrow">Editorial system</p>
          <h2>Taxonomy</h2>
          <p>Stable tags and categories can be reused across articles.</p>
        </div>
        <div className={styles.taxonomyColumns}>
          {taxonomyGroups.map((group) => (
            <section key={group.kind}>
              <h3>{group.title}</h3>
              <form onSubmit={(event) => void createTaxonomy(event, group.kind)}>
                <label>
                  <span className="sr-only">New {group.kind} name</span>
                  <input name="name" placeholder={`New ${group.kind}`} />
                </label>
                <Button type="submit" variant="secondary">
                  Add
                </Button>
              </form>
              <ul>
                {group.items.map((item) => (
                  <li key={item.id}>
                    <span>
                      <strong>{item.name}</strong>
                      <small>/{item.slug}</small>
                    </span>
                    <Button
                      aria-label={`Delete ${item.name}`}
                      onClick={() => void removeTaxonomy(item)}
                      variant="quiet"
                    >
                      Delete
                    </Button>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      </section>
    </div>
  );
}

"use client";

import type { Route } from "next";
import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import type { PageData } from "@/generated/api/src/models";
import { ApiError } from "@/lib/api";
import { adminPagesApi, type AdminPagesApiBoundary } from "./admin-api";
import styles from "./pages-admin.module.css";

const message = (value: unknown) =>
  value instanceof ApiError ? value.message : "The request could not be completed.";

export function PageManager({ api = adminPagesApi }: { api?: AdminPagesApiBoundary }) {
  const [pages, setPages] = useState<PageData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const router = useRouter();
  async function load() {
    setLoading(true);
    try {
      setPages(await api.list());
      setError("");
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
  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const title = String(data.get("title") ?? "").trim();
    const routeKind = String(data.get("routeKind")) as "home" | "custom";
    try {
      const page = await api.create({
        title,
        description: "A configurable page.",
        routeKind,
        slug: routeKind === "custom" ? String(data.get("slug") ?? "") : null,
        visible: true,
        navigationVisible: false,
      });
      router.push(`/admin/pages/${page.id}/edit` as Route);
    } catch (value) {
      setError(message(value));
    }
  }
  return (
    <div className={styles.manager}>
      <header className={styles.pageHeader}>
        <div>
          <p className="eyebrow">Composition system</p>
          <h1>Pages</h1>
          <p>Build the Home route and safe custom pages from the frozen block palette.</p>
        </div>
      </header>
      {error ? (
        <p role="alert" className={styles.error}>
          {error}
        </p>
      ) : null}
      <form className={styles.create} onSubmit={(event) => void create(event)}>
        <label>
          Page title
          <input name="title" required maxLength={120} />
        </label>
        <label>
          Route
          <select name="routeKind">
            <option value="custom">Custom</option>
            <option value="home">Home</option>
          </select>
        </label>
        <label>
          Slug
          <input name="slug" placeholder="case-studies" pattern="[a-z0-9-]+" />
        </label>
        <Button type="submit">Create page</Button>
      </form>
      {loading ? (
        <p>Loading pages…</p>
      ) : (
        <div className={styles.tableWrap}>
          <table>
            <thead>
              <tr>
                <th>Page</th>
                <th>Route</th>
                <th>State</th>
                <th>Blocks</th>
                <th>
                  <span className="sr-only">Action</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {pages.map((page) => (
                <tr key={page.id}>
                  <td>
                    <strong>{page.draft.title}</strong>
                    <small>Updated {page.updatedAt.toLocaleDateString()}</small>
                  </td>
                  <td>{page.routeKind === "home" ? "/" : `/${page.slug}`}</td>
                  <td>
                    <span className={styles.pill}>{page.lifecycle.replaceAll("_", " ")}</span>
                  </td>
                  <td>{page.draft.blocks.length}</td>
                  <td>
                    <Link href={`/admin/pages/${page.id}/edit` as Route}>Open builder</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

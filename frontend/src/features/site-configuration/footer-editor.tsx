"use client";

import { useCallback, useMemo, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { LoadingPanel } from "@/components/ui/loading-panel";
import {
  FooterItemKind,
  LinkKind,
  LinkTarget,
  type FooterColumnInput,
  type FooterData,
  type FooterItemInput,
  type FooterReplaceRequest,
} from "@/generated/api/src/models";
import { useAuth } from "@/features/auth/auth-context";
import { ApiError } from "@/lib/api";

import { adminSiteApi, type AdminSiteApiBoundary } from "./admin-api";
import {
  FormStatus,
  optional,
  toApiError,
  UnsavedChangesGuard,
  useDeferredInitialLoad,
} from "./configuration-form";
import styles from "./configuration.module.css";
import { revalidatePublicConfiguration } from "./revalidate-public";

interface FooterDraft {
  columns: FooterColumnInput[];
  copyrightText: string;
}

function draftFrom(data: FooterData): FooterDraft {
  return {
    copyrightText: data.copyrightText ?? "",
    columns: data.columns.map((column) => ({
      id: column.id,
      items: column.items.map((item) => ({
        href: item.href,
        id: item.id,
        itemKind: item.itemKind ?? FooterItemKind.Link,
        label: item.label,
        linkKind: item.linkKind,
        position: item.position,
        target: item.target ?? LinkTarget.SameWindow,
        visible: item.visible ?? true,
      })),
      position: column.position,
      title: column.title,
      visible: column.visible,
    })),
  };
}

function requestFrom(draft: FooterDraft): FooterReplaceRequest {
  return {
    copyrightText: optional(draft.copyrightText),
    columns: draft.columns.map((column, position) => ({
      ...column,
      position,
      items: column.items.map((item, itemPosition) => ({ ...item, position: itemPosition })),
    })),
  };
}

function move<Value>(values: Value[], index: number, direction: -1 | 1): Value[] {
  const other = index + direction;
  if (other < 0 || other >= values.length) return values;
  const next = [...values];
  const currentValue = next[index];
  const otherValue = next[other];
  if (currentValue === undefined || otherValue === undefined) return values;
  next[index] = otherValue;
  next[other] = currentValue;
  return next;
}

export function FooterEditor({ api = adminSiteApi }: { api?: AdminSiteApiBoundary }) {
  const auth = useAuth();
  const [draft, setDraft] = useState<FooterDraft | null>(null);
  const [etag, setEtag] = useState("");
  const [dirty, setDirty] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [saved, setSaved] = useState<string | null>(null);
  const retry = useRef<{ key: string; payload: string } | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resource = await api.getFooter();
      setDraft(draftFrom(resource.data));
      setEtag(resource.etag);
      setDirty(false);
      retry.current = null;
    } catch (caught) {
      const next = toApiError(caught);
      setError(next);
      if (next.status === 401) auth.expireSession();
    } finally {
      setLoading(false);
    }
  }, [api, auth]);

  useDeferredInitialLoad(load);

  const change = useCallback((next: FooterDraft) => {
    setDraft(next);
    setDirty(true);
    setSaved(null);
  }, []);

  const request = useMemo(() => (draft ? requestFrom(draft) : null), [draft]);
  const save = useCallback(async (): Promise<boolean> => {
    if (!request || !etag) return false;
    setSaving(true);
    setError(null);
    setSaved(null);
    const serialized = JSON.stringify(request);
    if (!retry.current || retry.current.payload !== serialized) {
      retry.current = { key: crypto.randomUUID(), payload: serialized };
    }
    try {
      const resource = await api.replaceFooter(request, etag, retry.current.key);
      setDraft(draftFrom(resource.data));
      setEtag(resource.etag);
      setDirty(false);
      retry.current = null;
      const refreshed = await revalidatePublicConfiguration("footer");
      setSaved(
        refreshed
          ? "Footer saved. Only visible columns and links appear in the refreshed footer."
          : "Footer saved. Public pages will refresh within one minute.",
      );
      return true;
    } catch (caught) {
      const next = toApiError(caught);
      setError(next);
      if (next.status === 401) auth.expireSession();
      return false;
    } finally {
      setSaving(false);
    }
  }, [api, auth, etag, request]);

  function updateColumn(id: string, patch: Partial<FooterColumnInput>) {
    if (!draft) return;
    change({
      ...draft,
      columns: draft.columns.map((column) => (column.id === id ? { ...column, ...patch } : column)),
    });
  }

  function updateItem(columnId: string, itemId: string, patch: Partial<FooterItemInput>) {
    if (!draft) return;
    change({
      ...draft,
      columns: draft.columns.map((column) =>
        column.id === columnId
          ? {
              ...column,
              items: column.items.map((item) =>
                item.id === itemId ? { ...item, ...patch } : item,
              ),
            }
          : column,
      ),
    });
  }

  if (loading) return <LoadingPanel label="Loading footer" />;
  if (!draft || !request) {
    return (
      <section className={styles.notice}>
        <p>The footer could not be loaded.</p>
        <Button onClick={() => void load()} variant="secondary">
          Try again
        </Button>
      </section>
    );
  }

  return (
    <>
      <header className={styles.pageHeader}>
        <div>
          <p className="eyebrow">Structure / Footer</p>
          <h1>Footer</h1>
          <p>
            Organize public destinations into visible columns with deterministic keyboard controls.
          </p>
        </div>
        <Button
          onClick={() =>
            change({
              ...draft,
              columns: [
                ...draft.columns,
                {
                  id: crypto.randomUUID(),
                  items: [],
                  position: draft.columns.length,
                  title: "New column",
                  visible: true,
                },
              ],
            })
          }
          type="button"
          variant="secondary"
        >
          Add column
        </Button>
      </header>
      <form
        className={styles.form}
        onSubmit={(event) => {
          event.preventDefault();
          void save();
        }}
      >
        <FormStatus error={error} saved={saved} />
        {error?.code === "RESOURCE_VERSION_CONFLICT" ? (
          <div className="button-row">
            <Button onClick={() => void load()} type="button" variant="secondary">
              Reload current version
            </Button>
            <Button
              onClick={() => void navigator.clipboard.writeText(JSON.stringify(request, null, 2))}
              type="button"
              variant="quiet"
            >
              Copy my changes
            </Button>
          </div>
        ) : null}
        <section className={styles.section}>
          <h2>Footer identity</h2>
          <label className={styles.field}>
            <span>Copyright or footer note</span>
            <input
              maxLength={240}
              onChange={(event) => change({ ...draft, copyrightText: event.target.value })}
              value={draft.copyrightText}
            />
          </label>
        </section>
        {draft.columns.length === 0 ? (
          <p className={styles.notice}>No footer columns are configured.</p>
        ) : null}
        {draft.columns.map((column, columnIndex) => (
          <section className={styles.section} key={column.id}>
            <div className={styles.itemHeader}>
              <h2>{column.title || "Untitled column"}</h2>
              <div className={styles.itemActions}>
                <Button
                  disabled={columnIndex === 0}
                  onClick={() =>
                    change({ ...draft, columns: move(draft.columns, columnIndex, -1) })
                  }
                  type="button"
                  variant="quiet"
                >
                  Move column up
                </Button>
                <Button
                  disabled={columnIndex === draft.columns.length - 1}
                  onClick={() => change({ ...draft, columns: move(draft.columns, columnIndex, 1) })}
                  type="button"
                  variant="quiet"
                >
                  Move column down
                </Button>
                <Button
                  onClick={() =>
                    change({
                      ...draft,
                      columns: draft.columns.filter((candidate) => candidate.id !== column.id),
                    })
                  }
                  type="button"
                  variant="danger"
                >
                  Remove column
                </Button>
              </div>
            </div>
            <div className={styles.fieldGrid}>
              <label className={styles.field}>
                <span>Column title</span>
                <input
                  maxLength={80}
                  onChange={(event) => updateColumn(column.id, { title: event.target.value })}
                  required
                  value={column.title}
                />
              </label>
              <label className={styles.checkbox}>
                <input
                  checked={column.visible ?? true}
                  onChange={(event) => updateColumn(column.id, { visible: event.target.checked })}
                  type="checkbox"
                />
                <span>Visible publicly</span>
              </label>
            </div>
            {column.items.map((item, itemIndex) => (
              <article className={styles.itemCard} key={item.id}>
                <div className={styles.itemHeader}>
                  <h3>{item.label || "Untitled link"}</h3>
                  <div className={styles.itemActions}>
                    <Button
                      disabled={itemIndex === 0}
                      onClick={() =>
                        updateColumn(column.id, { items: move(column.items, itemIndex, -1) })
                      }
                      type="button"
                      variant="quiet"
                    >
                      Move link up
                    </Button>
                    <Button
                      disabled={itemIndex === column.items.length - 1}
                      onClick={() =>
                        updateColumn(column.id, { items: move(column.items, itemIndex, 1) })
                      }
                      type="button"
                      variant="quiet"
                    >
                      Move link down
                    </Button>
                    <Button
                      onClick={() =>
                        updateColumn(column.id, {
                          items: column.items.filter((candidate) => candidate.id !== item.id),
                        })
                      }
                      type="button"
                      variant="danger"
                    >
                      Remove link
                    </Button>
                  </div>
                </div>
                <div className={styles.fieldGrid}>
                  <label className={styles.field}>
                    <span>Label</span>
                    <input
                      maxLength={80}
                      onChange={(event) =>
                        updateItem(column.id, item.id, { label: event.target.value })
                      }
                      required
                      value={item.label}
                    />
                  </label>
                  <label className={styles.field}>
                    <span>Category</span>
                    <select
                      onChange={(event) =>
                        updateItem(column.id, item.id, {
                          itemKind: event.target.value as FooterItemKind,
                        })
                      }
                      value={item.itemKind}
                    >
                      <option value={FooterItemKind.Link}>Link</option>
                      <option value={FooterItemKind.Social}>Social</option>
                      <option value={FooterItemKind.Legal}>Legal</option>
                    </select>
                  </label>
                  <label className={styles.field}>
                    <span>Link type</span>
                    <select
                      onChange={(event) => {
                        const linkKind = event.target.value as FooterItemInput["linkKind"];
                        updateItem(column.id, item.id, {
                          linkKind,
                          ...(linkKind === LinkKind.Internal
                            ? { target: LinkTarget.SameWindow }
                            : {}),
                        });
                      }}
                      value={item.linkKind}
                    >
                      <option value={LinkKind.Internal}>Internal</option>
                      <option value={LinkKind.External}>External HTTPS</option>
                    </select>
                  </label>
                  <label className={styles.field}>
                    <span>Destination</span>
                    <input
                      onChange={(event) =>
                        updateItem(column.id, item.id, { href: event.target.value })
                      }
                      required
                      value={item.href}
                    />
                  </label>
                  <label className={styles.field}>
                    <span>Open in</span>
                    <select
                      disabled={item.linkKind === LinkKind.Internal}
                      onChange={(event) =>
                        updateItem(column.id, item.id, {
                          target: event.target.value as LinkTarget,
                        })
                      }
                      value={item.target}
                    >
                      <option value={LinkTarget.SameWindow}>Same window</option>
                      <option value={LinkTarget.NewWindow}>New window</option>
                    </select>
                  </label>
                  <label className={styles.checkbox}>
                    <input
                      checked={item.visible ?? true}
                      onChange={(event) =>
                        updateItem(column.id, item.id, { visible: event.target.checked })
                      }
                      type="checkbox"
                    />
                    <span>Visible publicly</span>
                  </label>
                </div>
              </article>
            ))}
            <Button
              onClick={() =>
                updateColumn(column.id, {
                  items: [
                    ...column.items,
                    {
                      href: "/about",
                      id: crypto.randomUUID(),
                      itemKind: FooterItemKind.Link,
                      label: "New link",
                      linkKind: LinkKind.Internal,
                      position: column.items.length,
                      target: LinkTarget.SameWindow,
                      visible: true,
                    },
                  ],
                })
              }
              type="button"
              variant="secondary"
            >
              Add link to {column.title}
            </Button>
          </section>
        ))}
        <div className={styles.actionBar}>
          <Button disabled={saving} type="submit">
            {saving ? "Saving…" : "Save footer"}
          </Button>
          <Button
            disabled={!dirty || saving}
            onClick={() => void load()}
            type="button"
            variant="quiet"
          >
            Discard changes
          </Button>
          <UnsavedChangesGuard dirty={dirty} onSave={save} />
        </div>
      </form>
    </>
  );
}

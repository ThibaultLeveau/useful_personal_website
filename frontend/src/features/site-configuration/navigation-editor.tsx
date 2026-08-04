"use client";

import { useCallback, useMemo, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { LoadingPanel } from "@/components/ui/loading-panel";
import {
  LinkKind,
  LinkTarget,
  type NavigationData,
  type NavigationItemInput,
  type NavigationReplaceRequest,
} from "@/generated/api/src/models";
import { useAuth } from "@/features/auth/auth-context";
import { ApiError } from "@/lib/api";

import { adminSiteApi, type AdminSiteApiBoundary } from "./admin-api";
import {
  FormStatus,
  toApiError,
  UnsavedChangesGuard,
  useDeferredInitialLoad,
} from "./configuration-form";
import styles from "./configuration.module.css";
import { revalidatePublicConfiguration } from "./revalidate-public";

function editable(data: NavigationData): NavigationItemInput[] {
  return data.items.map((item) => ({
    href: item.href,
    id: item.id,
    label: item.label,
    linkKind: item.linkKind,
    parentId: item.parentId ?? null,
    position: item.position,
    target: item.target ?? LinkTarget.SameWindow,
    visible: item.visible ?? true,
  }));
}

function ordered(items: NavigationItemInput[]): NavigationItemInput[] {
  const roots = items.filter((item) => !item.parentId);
  return roots.flatMap((root, rootPosition) => [
    { ...root, parentId: null, position: rootPosition },
    ...items
      .filter((item) => item.parentId === root.id)
      .map((item, position) => ({ ...item, position })),
  ]);
}

function requestFor(items: NavigationItemInput[]): NavigationReplaceRequest {
  return { items: ordered(items) };
}

export function NavigationEditor({ api = adminSiteApi }: { api?: AdminSiteApiBoundary }) {
  const auth = useAuth();
  const [items, setItems] = useState<NavigationItemInput[] | null>(null);
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
      const resource = await api.getNavigation();
      setItems(editable(resource.data));
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

  const change = useCallback((next: NavigationItemInput[]) => {
    setItems(next);
    setDirty(true);
    setSaved(null);
  }, []);

  const request = useMemo(() => (items ? requestFor(items) : null), [items]);
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
      const resource = await api.replaceNavigation(request, etag, retry.current.key);
      setItems(editable(resource.data));
      setEtag(resource.etag);
      setDirty(false);
      retry.current = null;
      const refreshed = await revalidatePublicConfiguration("navigation");
      setSaved(
        refreshed
          ? "Navigation saved. Hidden destinations are absent from the refreshed public menu."
          : "Navigation saved. Public pages will refresh within one minute.",
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

  function updateItem(id: string, patch: Partial<NavigationItemInput>) {
    if (!items) return;
    change(items.map((item) => (item.id === id ? { ...item, ...patch } : item)));
  }

  function moveItem(id: string, direction: -1 | 1) {
    if (!items) return;
    const current = items.find((item) => item.id === id);
    if (!current) return;
    const siblings = items.filter((item) => (item.parentId ?? null) === (current.parentId ?? null));
    const currentIndex = siblings.findIndex((item) => item.id === id);
    const other = siblings[currentIndex + direction];
    if (!other) return;
    const firstIndex = items.findIndex((item) => item.id === current.id);
    const secondIndex = items.findIndex((item) => item.id === other.id);
    const next = [...items];
    next[firstIndex] = other;
    next[secondIndex] = current;
    change(next);
  }

  if (loading) return <LoadingPanel label="Loading navigation" />;
  if (!items || !request) {
    return (
      <section className={styles.notice}>
        <p>The navigation could not be loaded.</p>
        <Button onClick={() => void load()} variant="secondary">
          Try again
        </Button>
      </section>
    );
  }
  const roots = items.filter((item) => !item.parentId);

  return (
    <>
      <header className={styles.pageHeader}>
        <div>
          <p className="eyebrow">Structure / Navigation</p>
          <h1>Primary navigation</h1>
          <p>
            Build a deterministic two-level menu. Internal paths must resolve to a registered page.
          </p>
        </div>
        <Button
          onClick={() =>
            change([
              ...items,
              {
                href: "/",
                id: crypto.randomUUID(),
                label: "New destination",
                linkKind: LinkKind.Internal,
                parentId: null,
                position: roots.length,
                target: LinkTarget.SameWindow,
                visible: true,
              },
            ])
          }
          type="button"
          variant="secondary"
        >
          Add destination
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
        <section aria-label="Navigation destinations" className={styles.section}>
          {items.length === 0 ? (
            <p className={styles.notice}>No public navigation destinations are configured.</p>
          ) : null}
          {ordered(items).map((item) => {
            const siblings = items.filter(
              (candidate) => (candidate.parentId ?? null) === (item.parentId ?? null),
            );
            const siblingIndex = siblings.findIndex((candidate) => candidate.id === item.id);
            const hasChildren = items.some((candidate) => candidate.parentId === item.id);
            return (
              <article className={styles.itemCard} key={item.id}>
                <div className={styles.itemHeader}>
                  <h2>{item.label || "Untitled destination"}</h2>
                  <div className={styles.itemActions}>
                    <Button
                      aria-label={`Move ${item.label} up`}
                      disabled={siblingIndex === 0}
                      onClick={() => moveItem(item.id, -1)}
                      type="button"
                      variant="quiet"
                    >
                      Move up
                    </Button>
                    <Button
                      aria-label={`Move ${item.label} down`}
                      disabled={siblingIndex === siblings.length - 1}
                      onClick={() => moveItem(item.id, 1)}
                      type="button"
                      variant="quiet"
                    >
                      Move down
                    </Button>
                    <Button
                      onClick={() =>
                        change(
                          items.filter(
                            (candidate) =>
                              candidate.id !== item.id && candidate.parentId !== item.id,
                          ),
                        )
                      }
                      type="button"
                      variant="danger"
                    >
                      Remove
                    </Button>
                  </div>
                </div>
                <div className={styles.fieldGrid}>
                  <label className={styles.field}>
                    <span>Label</span>
                    <input
                      maxLength={80}
                      onChange={(event) => updateItem(item.id, { label: event.target.value })}
                      required
                      value={item.label}
                    />
                  </label>
                  <label className={styles.field}>
                    <span>Parent</span>
                    <select
                      disabled={hasChildren}
                      onChange={(event) =>
                        updateItem(item.id, { parentId: event.target.value || null })
                      }
                      value={item.parentId ?? ""}
                    >
                      <option value="">Top level</option>
                      {roots
                        .filter((root) => root.id !== item.id)
                        .map((root) => (
                          <option key={root.id} value={root.id}>
                            {root.label}
                          </option>
                        ))}
                    </select>
                    {hasChildren ? (
                      <small>Remove or move child destinations before nesting this item.</small>
                    ) : null}
                  </label>
                  <label className={styles.field}>
                    <span>Link type</span>
                    <select
                      onChange={(event) => {
                        const linkKind = event.target.value as NavigationItemInput["linkKind"];
                        updateItem(item.id, {
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
                      onChange={(event) => updateItem(item.id, { href: event.target.value })}
                      required
                      value={item.href}
                    />
                  </label>
                  <label className={styles.field}>
                    <span>Open in</span>
                    <select
                      disabled={item.linkKind === LinkKind.Internal}
                      onChange={(event) =>
                        updateItem(item.id, {
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
                      onChange={(event) => updateItem(item.id, { visible: event.target.checked })}
                      type="checkbox"
                    />
                    <span>Visible publicly</span>
                  </label>
                </div>
              </article>
            );
          })}
        </section>
        <div className={styles.actionBar}>
          <Button disabled={saving} type="submit">
            {saving ? "Saving…" : "Save navigation"}
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

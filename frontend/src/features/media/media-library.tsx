"use client";

import { useCallback, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { LoadingPanel } from "@/components/ui/loading-panel";
import type { MediaAssetData, MediaUsageData, PaginationData } from "@/generated/api/src/models";
import { useAuth } from "@/features/auth/auth-context";
import {
  FormStatus,
  toApiError,
  useDeferredInitialLoad,
} from "@/features/site-configuration/configuration-form";
import { ApiError } from "@/lib/api";

import { adminMediaApi, type AdminMediaApiBoundary } from "./admin-api";
import styles from "./media-library.module.css";

const bytes = new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 });
const date = new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short" });

function previewUrl(asset: MediaAssetData): string | undefined {
  const webp = asset.variants
    .filter((variant) => variant.format === "webp")
    .sort((left, right) => Math.abs(left.width - 640) - Math.abs(right.width - 640))[0];
  return webp?.adminUrl ?? asset.variants[0]?.adminUrl;
}

function usageLabel(usage: MediaUsageData): string {
  return `${usage.ownerType.replaceAll("_", " ")} / ${usage.role.replaceAll("_", " ")}`;
}

export function MediaLibrary({ api = adminMediaApi }: { api?: AdminMediaApiBoundary }) {
  const auth = useAuth();
  const [items, setItems] = useState<MediaAssetData[]>([]);
  const [pagination, setPagination] = useState<PaginationData | null>(null);
  const [selected, setSelected] = useState<MediaAssetData | null>(null);
  const [usages, setUsages] = useState<MediaUsageData[]>([]);
  const [usageLoading, setUsageLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [progress, setProgress] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [saved, setSaved] = useState<string | null>(null);

  const load = useCallback(
    async (nextPage = 1, nextSearch = "") => {
      setLoading(true);
      setError(null);
      try {
        const snapshot = await api.list({
          page: nextPage,
          pageSize: 20,
          ...(nextSearch.trim() ? { search: nextSearch.trim() } : {}),
        });
        setItems(snapshot.items);
        setPagination(snapshot.pagination);
        setPage(snapshot.pagination.page);
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

  async function select(asset: MediaAssetData) {
    setSelected(asset);
    setUsages([]);
    setUsageLoading(true);
    setError(null);
    try {
      setUsages(await api.usage(asset.id));
    } catch (caught) {
      const next = toApiError(caught);
      setError(next);
      if (next.status === 401) auth.expireSession();
    } finally {
      setUsageLoading(false);
    }
  }

  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const file = form.get("file");
    if (!(file instanceof File) || file.size === 0) return;
    setBusy(true);
    setError(null);
    setSaved(null);
    setProgress(0);
    try {
      const created = await api.upload(file, { onProgress: setProgress });
      formElement.reset();
      setSaved(`${created.displayName} uploaded and verified.`);
      await load(1, search);
      await select(created);
    } catch (caught) {
      const next = toApiError(caught);
      setError(next);
      if (next.status === 401) auth.expireSession();
    } finally {
      setBusy(false);
      setProgress(null);
    }
  }

  async function rename(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const displayName = String(new FormData(event.currentTarget).get("displayName") ?? "").trim();
    if (!displayName) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await api.rename(selected, displayName);
      setSelected(updated);
      setItems((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      setSaved("Display name saved.");
    } catch (caught) {
      const next = toApiError(caught);
      setError(next);
      if (next.status === 401) auth.expireSession();
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    if (!selected || usages.some((usage) => usage.active)) return;
    if (!window.confirm(`Delete ${selected.displayName}? This cannot be undone.`)) return;
    setBusy(true);
    setError(null);
    try {
      await api.delete(selected);
      setSaved("Media deleted.");
      setSelected(null);
      setUsages([]);
      await load(page, search);
    } catch (caught) {
      const next = toApiError(caught);
      setError(next);
      if (next.status === 401) auth.expireSession();
    } finally {
      setBusy(false);
    }
  }

  if (loading && items.length === 0) return <LoadingPanel label="Loading media library" />;
  const activeUsages = usages.filter((usage) => usage.active);

  return (
    <div className={styles.library}>
      <header className={styles.pageHeader}>
        <div>
          <p className="eyebrow">Content / Media</p>
          <h1>Media library</h1>
          <p>Upload verified images, inspect exact usage, and manage safe display metadata.</p>
        </div>
        <Button
          disabled={loading || busy}
          onClick={() => void load(page, search)}
          variant="secondary"
        >
          Refresh
        </Button>
      </header>
      <FormStatus error={error} saved={saved} />

      <form className={styles.upload} onSubmit={(event) => void upload(event)}>
        <div>
          <label htmlFor="media-file">Upload image</label>
          <p>JPEG, PNG, or WebP. Maximum 10 MiB and 6000 px per dimension.</p>
        </div>
        <input
          accept="image/jpeg,image/png,image/webp"
          disabled={busy}
          id="media-file"
          name="file"
          required
          type="file"
        />
        <Button disabled={busy} type="submit">
          Upload
        </Button>
        {progress === null ? null : (
          <div
            className={styles.progress}
            aria-label={`Upload ${progress}%`}
            role="progressbar"
            aria-valuemax={100}
            aria-valuemin={0}
            aria-valuenow={progress}
          >
            <span style={{ width: `${progress}%` }} />
          </div>
        )}
      </form>

      <form
        className={styles.toolbar}
        onSubmit={(event) => {
          event.preventDefault();
          void load(1, search);
        }}
      >
        <label htmlFor="media-search">Search display names</label>
        <input
          id="media-search"
          maxLength={120}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search media"
          value={search}
        />
        <Button disabled={loading} type="submit" variant="secondary">
          Search
        </Button>
      </form>

      <div className={styles.workspace}>
        <section aria-labelledby="media-results-title">
          <div className={styles.sectionHeader}>
            <h2 id="media-results-title">Images</h2>
            <span>{pagination?.totalItems ?? items.length} total</span>
          </div>
          {items.length === 0 ? (
            <p className={styles.empty}>No media matches this view.</p>
          ) : (
            <ul className={styles.grid}>
              {items.map((asset) => (
                <li key={asset.id}>
                  <button
                    aria-pressed={selected?.id === asset.id}
                    onClick={() => void select(asset)}
                    type="button"
                  >
                    {previewUrl(asset) ? (
                      // Private previews cannot pass through the unauthenticated Next image optimizer.
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        alt=""
                        height={asset.height ?? 180}
                        loading="lazy"
                        src={previewUrl(asset)}
                        width={asset.width ?? 240}
                      />
                    ) : (
                      <span className={styles.unavailable}>Preview unavailable</span>
                    )}
                    <strong>{asset.displayName}</strong>
                    <small>
                      {asset.width ?? "—"} × {asset.height ?? "—"} ·{" "}
                      {asset.byteSize ? bytes.format(asset.byteSize) : "—"} B
                    </small>
                    <span className={styles.status}>{asset.status}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
          <nav className={styles.pagination} aria-label="Media pages">
            <Button
              disabled={!pagination?.hasPrevious || loading}
              onClick={() => void load(page - 1, search)}
              variant="secondary"
            >
              Previous
            </Button>
            <span>
              Page {pagination?.page ?? 1} of {pagination?.totalPages ?? 1}
            </span>
            <Button
              disabled={!pagination?.hasNext || loading}
              onClick={() => void load(page + 1, search)}
              variant="secondary"
            >
              Next
            </Button>
          </nav>
        </section>

        <aside className={styles.inspector} aria-labelledby="media-inspector-title">
          <h2 id="media-inspector-title">Inspector</h2>
          {selected ? (
            <>
              {previewUrl(selected) ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  alt=""
                  height={selected.height ?? 320}
                  src={previewUrl(selected)}
                  width={selected.width ?? 480}
                />
              ) : null}
              <form className={styles.rename} onSubmit={(event) => void rename(event)}>
                <label htmlFor="media-display-name">Display name</label>
                <input
                  defaultValue={selected.displayName}
                  id="media-display-name"
                  key={`${selected.id}-${selected.version}`}
                  maxLength={180}
                  name="displayName"
                  required
                />
                <Button disabled={busy} type="submit" variant="secondary">
                  Save name
                </Button>
              </form>
              <dl className={styles.facts}>
                <div>
                  <dt>Created</dt>
                  <dd>{date.format(selected.createdAt)}</dd>
                </div>
                <div>
                  <dt>Format</dt>
                  <dd>{selected.detectedFormat ?? "Unknown"}</dd>
                </div>
                <div>
                  <dt>Dimensions</dt>
                  <dd>
                    {selected.width ?? "—"} × {selected.height ?? "—"}
                  </dd>
                </div>
                <div>
                  <dt>Renditions</dt>
                  <dd>{selected.variants.length}</dd>
                </div>
              </dl>
              <section className={styles.usage} aria-labelledby="media-usage-title">
                <h3 id="media-usage-title">Usage</h3>
                {usageLoading ? (
                  <p>Loading usage…</p>
                ) : usages.length === 0 ? (
                  <p>Not currently assigned.</p>
                ) : (
                  <ul>
                    {usages.map((usage) => (
                      <li
                        key={`${usage.ownerType}-${usage.ownerId}-${usage.role}-${usage.position}`}
                      >
                        <strong>{usageLabel(usage)}</strong>
                        <span>
                          {usage.active ? "Active" : "Inactive"}
                          {usage._public ? " · Public" : ""}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
              <p className={styles.contextNote}>
                Alternative text and captions belong to each content usage and are set in the media
                picker.
              </p>
              <Button
                disabled={busy || usageLoading || activeUsages.length > 0}
                onClick={() => void remove()}
                variant="danger"
              >
                Delete media
              </Button>
              {activeUsages.length > 0 ? (
                <p className={styles.deleteNote}>
                  Remove all active usages before deleting this asset.
                </p>
              ) : null}
            </>
          ) : (
            <p className={styles.empty}>Select an image to inspect it.</p>
          )}
        </aside>
      </div>
    </div>
  );
}

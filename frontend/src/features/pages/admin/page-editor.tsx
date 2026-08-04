"use client";

import type { Route } from "next";
import Link from "next/link";
import { useEffect, useMemo, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import type {
  Block,
  BlockData,
  BlockType,
  PageData,
  PagePreviewData,
  RegistryData,
} from "@/generated/api/src/models";
import { adminMediaApi, type AdminMediaApiBoundary } from "@/features/media/admin-api";
import { MediaPicker } from "@/features/media/media-picker";
import { ApiError } from "@/lib/api";
import { adminPagesApi, type AdminPagesApiBoundary } from "./admin-api";
import { BLOCK_TYPES, newBlock } from "./block-catalog";
import styles from "./pages-admin.module.css";

const message = (value: unknown) =>
  value instanceof ApiError ? value.message : "The request could not be completed.";
const label = (value: string) => value.replaceAll("_", " ");

function MetadataEditor({
  page,
  save,
}: {
  page: PageData;
  save: (data: FormData) => Promise<void>;
}) {
  return (
    <form
      className={styles.metadata}
      onSubmit={(event) => {
        event.preventDefault();
        void save(new FormData(event.currentTarget));
      }}
    >
      <h2>Page settings</h2>
      <label>
        Title
        <input name="title" defaultValue={page.draft.title} required />
      </label>
      <label>
        Description
        <textarea name="description" defaultValue={page.draft.description} rows={3} required />
      </label>
      <div className={styles.fieldRow}>
        <label>
          Route
          <select name="routeKind" defaultValue={page.routeKind}>
            <option value="home">Home</option>
            <option value="custom">Custom</option>
          </select>
        </label>
        <label>
          Slug
          <input name="slug" defaultValue={page.slug ?? ""} />
        </label>
      </div>
      <label>
        SEO title
        <input name="seoTitle" defaultValue={page.draft.seoTitle ?? ""} />
      </label>
      <label>
        SEO description
        <textarea name="seoDescription" defaultValue={page.draft.seoDescription ?? ""} rows={2} />
      </label>
      <label>
        Canonical URL
        <input name="canonicalUrl" type="url" defaultValue={page.draft.canonicalUrl ?? ""} />
      </label>
      <div className={styles.checks}>
        <label>
          <input name="visible" type="checkbox" defaultChecked={page.visible} /> Public visibility
        </label>
        <label>
          <input name="navigationVisible" type="checkbox" defaultChecked={page.navigationVisible} />{" "}
          Navigation visibility
        </label>
      </div>
      <Button type="submit">Save settings</Button>
    </form>
  );
}

function BlockProperties({
  block,
  mediaApi,
  save,
}: {
  block: BlockData;
  mediaApi: AdminMediaApiBoundary;
  save: (next: Block) => Promise<void>;
}) {
  const [config, setConfig] = useState(() => JSON.stringify(block.definition.config, null, 2));
  const [mediaId, setMediaId] = useState<string | null>(() => {
    const value = block.definition.config as { mediaId?: unknown };
    return typeof value.mediaId === "string" ? value.mediaId : null;
  });
  const [parseError, setParseError] = useState("");
  const isMediaBlock =
    block.definition.blockType === "image" || block.definition.blockType === "image_with_text";
  function selectMedia(value: string | null) {
    try {
      const next = JSON.parse(config) as Record<string, unknown>;
      if (value) next.mediaId = value;
      else delete next.mediaId;
      setConfig(JSON.stringify(next, null, 2));
      setMediaId(value);
      setParseError("");
    } catch {
      setParseError("Fix the configuration JSON before changing its image.");
    }
  }
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    try {
      const next = {
        ...block.definition,
        title: String(data.get("title") ?? "") || null,
        subtitle: String(data.get("subtitle") ?? "") || null,
        description: String(data.get("description") ?? "") || null,
        layout: String(data.get("layout")),
        theme: String(data.get("theme")),
        config: JSON.parse(config),
      } as Block;
      setParseError("");
      void save(next);
    } catch {
      setParseError("Config must be valid JSON matching this block's generated schema.");
    }
  }
  return (
    <form className={styles.properties} onSubmit={submit}>
      <p className="eyebrow">Properties</p>
      <h2>{label(block.definition.blockType)}</h2>
      <label>
        Section title
        <input name="title" defaultValue={block.definition.title ?? ""} />
      </label>
      <label>
        Subtitle
        <input name="subtitle" defaultValue={block.definition.subtitle ?? ""} />
      </label>
      <label>
        Description
        <textarea name="description" defaultValue={block.definition.description ?? ""} rows={2} />
      </label>
      <div className={styles.fieldRow}>
        <label>
          Layout
          <select name="layout" defaultValue={block.definition.layout ?? "full"}>
            <option value="full">Full</option>
            <option value="contained">Contained</option>
            <option value="wide">Wide</option>
          </select>
        </label>
        <label>
          Theme
          <select name="theme" defaultValue={block.definition.theme ?? "default"}>
            <option value="default">Default</option>
            <option value="accent">Accent</option>
            <option value="muted">Muted</option>
            <option value="contrast">Contrast</option>
          </select>
        </label>
      </div>
      {isMediaBlock ? (
        <MediaPicker
          api={mediaApi}
          description="Choose a ready private-library asset. It becomes public only with this published block."
          label="Block image"
          onChange={selectMedia}
          value={mediaId}
        />
      ) : null}
      <label>
        Typed configuration
        <textarea
          aria-describedby="config-help"
          className={styles.code}
          value={config}
          onChange={(event) => setConfig(event.target.value)}
          rows={14}
          spellCheck={false}
        />
      </label>
      <small id="config-help">
        Strictly validated by the API. Unknown fields and unsafe URLs are rejected.
      </small>
      {parseError ? (
        <p role="alert" className={styles.error}>
          {parseError}
        </p>
      ) : null}
      <Button type="submit">Save block</Button>
    </form>
  );
}

export function PageEditor({
  pageId,
  api = adminPagesApi,
  mediaApi = adminMediaApi,
}: {
  pageId: string;
  api?: AdminPagesApiBoundary;
  mediaApi?: AdminMediaApiBoundary;
}) {
  const [page, setPage] = useState<PageData | null>(null);
  const [registry, setRegistry] = useState<RegistryData | null>(null);
  const [preview, setPreview] = useState<PagePreviewData | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [pendingMediaBlockType, setPendingMediaBlockType] = useState<BlockType | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const router = useRouter();
  const selected = useMemo(
    () => page?.draft.blocks.find((block) => block.id === selectedId) ?? null,
    [page, selectedId],
  );
  async function load() {
    try {
      const [next, manifest] = await Promise.all([api.get(pageId), api.registry()]);
      setPage(next);
      setRegistry(manifest);
      setSelectedId((current) => current ?? next.draft.blocks[0]?.id ?? null);
      setError("");
    } catch (value) {
      setError(message(value));
    }
  }
  useEffect(() => {
    const handle = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(handle);
  }, [pageId]); // eslint-disable-line react-hooks/exhaustive-deps
  async function mutate(operation: (current: PageData) => Promise<PageData>) {
    if (!page) return;
    setBusy(true);
    try {
      const next = await operation(page);
      setPage(next);
      setPreview(null);
      setError("");
    } catch (value) {
      setError(message(value));
    } finally {
      setBusy(false);
    }
  }
  async function showPreview() {
    if (!page) return;
    setBusy(true);
    try {
      setPreview(await api.preview(page.id));
      setError("");
    } catch (value) {
      setError(message(value));
    } finally {
      setBusy(false);
    }
  }
  function move(block: BlockData, offset: number) {
    if (!page) return;
    const ordered = page.draft.blocks.map((item) => item.id);
    const index = ordered.indexOf(block.id);
    const target = Math.max(0, Math.min(ordered.length - 1, index + offset));
    ordered.splice(index, 1);
    ordered.splice(target, 0, block.id);
    void mutate((current) => api.reorder(current, ordered));
  }
  async function exportPage() {
    if (!page) return;
    try {
      const data = await api.exportPage(page.id);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${page.slug ?? "home"}-page.json`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (value) {
      setError(message(value));
    }
  }
  function schedulePage() {
    const value = window.prompt(
      "Publish at (ISO 8601 with timezone)",
      new Date(Date.now() + 86_400_000).toISOString(),
    );
    if (!value) return;
    const publishAt = new Date(value);
    if (Number.isNaN(publishAt.getTime())) {
      setError("Enter a valid ISO 8601 date and time.");
      return;
    }
    void mutate((current) =>
      current.lifecycle === "scheduled"
        ? api.reschedule(current, publishAt)
        : api.publish(current, publishAt),
    );
  }
  if (!page)
    return (
      <div className={styles.manager}>
        {error ? (
          <p role="alert" className={styles.error}>
            {error}
          </p>
        ) : (
          <p>Loading page builder…</p>
        )}
      </div>
    );
  return (
    <div className={styles.editor}>
      <header className={styles.editorHeader}>
        <div>
          <Link href={"/admin/pages" as Route}>← Pages</Link>
          <p className="eyebrow">{page.routeKind === "home" ? "Home" : `/${page.slug}`}</p>
          <h1>{page.draft.title}</h1>
        </div>
        <div className={styles.status}>
          <span className={styles.pill}>{label(page.lifecycle)}</span>
          <span>v{page.version}</span>
        </div>
      </header>
      {error ? (
        <p role="alert" className={styles.error}>
          {error}
        </p>
      ) : null}
      <div className={styles.builder}>
        <aside className={styles.palette}>
          <h2>Blocks</h2>
          <p>{registry?.entries.length ?? 0} validated components</p>
          <div className={styles.paletteGrid}>
            {BLOCK_TYPES.map((type) => (
              <Button
                disabled={busy || !registry?.entries.some((entry) => entry.blockType === type)}
                key={type}
                onClick={() => {
                  if (type === "image" || type === "image_with_text") {
                    setPendingMediaBlockType(type);
                    return;
                  }
                  void mutate((current) => api.addBlock(current, newBlock(type)));
                }}
                variant="secondary"
              >
                <span>{label(type)}</span>
                <small>{registry?.entries.find((entry) => entry.blockType === type)?.group}</small>
              </Button>
            ))}
          </div>
          {pendingMediaBlockType ? (
            <div className={styles.pendingMedia}>
              <MediaPicker
                api={mediaApi}
                description={`Choose the ready asset for this new ${label(pendingMediaBlockType)} block.`}
                disabled={busy}
                label="New block image"
                onChange={(assetId) => {
                  if (!assetId) return;
                  const type = pendingMediaBlockType;
                  setPendingMediaBlockType(null);
                  void mutate((current) => api.addBlock(current, newBlock(type, assetId)));
                }}
                value={null}
              />
              <Button onClick={() => setPendingMediaBlockType(null)} variant="quiet">
                Cancel
              </Button>
            </div>
          ) : null}
        </aside>
        <main className={styles.canvas} aria-label="Page canvas">
          <div className={styles.canvasTop}>
            <div>
              <p className="eyebrow">Draft canvas</p>
              <h2>{page.draft.title}</h2>
              <p>{page.draft.description || "Add a description in page settings."}</p>
            </div>
            <Button onClick={() => void showPreview()} variant="secondary">
              Check preview
            </Button>
          </div>
          {preview?.issues.length ? (
            <section className={styles.issues} aria-label="Publication issues">
              <h3>
                {preview.issues.length} publication issue{preview.issues.length === 1 ? "" : "s"}
              </h3>
              {preview.issues.map((issue) => (
                <button
                  key={`${issue.blockId}-${issue.path}`}
                  onClick={() => {
                    setSelectedId(issue.blockId);
                    document.getElementById(`builder-block-${issue.blockId}`)?.focus();
                  }}
                >
                  <strong>{label(issue.code)}</strong>
                  <span>{issue.path}</span>
                </button>
              ))}
            </section>
          ) : preview ? (
            <p className={styles.ready}>Preview passed publication checks.</p>
          ) : null}
          <ol className={styles.blockList}>
            {page.draft.blocks.map((block, index) => (
              <li
                className={selectedId === block.id ? styles.selected : ""}
                id={`builder-block-${block.id}`}
                key={block.id}
                tabIndex={-1}
              >
                <button className={styles.blockSelect} onClick={() => setSelectedId(block.id)}>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <strong>{block.definition.title || label(block.definition.blockType)}</strong>
                  <small>
                    {block.definition.visible === false
                      ? "Hidden"
                      : label(block.definition.blockType)}
                  </small>
                </button>
                <div className={styles.blockActions}>
                  <Button
                    aria-label={`Move ${label(block.definition.blockType)} up`}
                    disabled={index === 0 || busy}
                    onClick={() => move(block, -1)}
                    variant="quiet"
                  >
                    ↑
                  </Button>
                  <Button
                    aria-label={`Move ${label(block.definition.blockType)} down`}
                    disabled={index === page.draft.blocks.length - 1 || busy}
                    onClick={() => move(block, 1)}
                    variant="quiet"
                  >
                    ↓
                  </Button>
                  <Button
                    onClick={() => void mutate((current) => api.duplicateBlock(current, block.id))}
                    variant="quiet"
                  >
                    Duplicate
                  </Button>
                  <Button
                    onClick={() =>
                      void mutate((current) =>
                        api.setBlockVisibility(
                          current,
                          block.id,
                          block.definition.visible === false,
                        ),
                      )
                    }
                    variant="quiet"
                  >
                    {block.definition.visible === false ? "Show" : "Hide"}
                  </Button>
                  <Button
                    onClick={() => {
                      if (window.confirm("Delete this draft block?"))
                        void mutate((current) => api.deleteBlock(current, block.id));
                    }}
                    variant="quiet"
                  >
                    Delete
                  </Button>
                </div>
              </li>
            ))}
          </ol>
          {page.draft.blocks.length === 0 ? (
            <div className={styles.empty}>
              <h3>Begin with a block</h3>
              <p>Choose from the palette. The order here is the public reading order.</p>
            </div>
          ) : null}
        </main>
        <aside className={styles.inspector}>
          {selected ? (
            <BlockProperties
              block={selected}
              key={`${selected.id}-${page.version}`}
              mediaApi={mediaApi}
              save={(next) => mutate((current) => api.updateBlock(current, selected.id, next))}
            />
          ) : (
            <MetadataEditor
              page={page}
              save={(data) =>
                mutate((current) =>
                  api.save(current, {
                    title: String(data.get("title")),
                    description: String(data.get("description")),
                    routeKind: String(data.get("routeKind")) as "home" | "custom",
                    slug: String(data.get("slug")) || null,
                    seoTitle: String(data.get("seoTitle")) || null,
                    seoDescription: String(data.get("seoDescription")) || null,
                    canonicalUrl: String(data.get("canonicalUrl")) || null,
                    visible: data.get("visible") === "on",
                    navigationVisible: data.get("navigationVisible") === "on",
                  }),
                )
              }
            />
          )}
          <Button onClick={() => setSelectedId(null)} variant="quiet">
            Edit page settings
          </Button>
        </aside>
      </div>
      <footer className={styles.actionBar}>
        <div>
          <strong>{page.draft.blocks.length} blocks</strong>
          <span>{page.updatedAt.toLocaleTimeString()}</span>
        </div>
        <div>
          <Button onClick={() => void exportPage()} variant="quiet">
            Export
          </Button>
          {page.routeKind === "custom" ? (
            <Button
              onClick={() => {
                const slug = window.prompt(
                  "Slug for the duplicated page",
                  `${page.slug ?? "page"}-copy`,
                );
                if (slug) void mutate((current) => api.duplicate(current, slug));
              }}
              variant="secondary"
            >
              Duplicate page
            </Button>
          ) : null}
          {page.lifecycle === "published" || page.lifecycle === "scheduled" ? (
            <Button
              onClick={() => void mutate((current) => api.unpublish(current))}
              variant="secondary"
            >
              Unpublish
            </Button>
          ) : null}
          <Button disabled={busy} onClick={() => void mutate((current) => api.publish(current))}>
            Publish now
          </Button>
          <Button disabled={busy} onClick={schedulePage} variant="secondary">
            {page.lifecycle === "scheduled" ? "Reschedule" : "Schedule"}
          </Button>
          {page.routeKind === "custom" ? (
            <Button
              onClick={() => {
                if (window.confirm("Delete this page?"))
                  void api
                    .remove(page)
                    .then(() => router.push("/admin/pages" as Route))
                    .catch((value: unknown) => setError(message(value)));
              }}
              variant="quiet"
            >
              Delete
            </Button>
          ) : null}
        </div>
      </footer>
    </div>
  );
}

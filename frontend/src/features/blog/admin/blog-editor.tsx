"use client";

import type { Route } from "next";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import type {
  PostData,
  PostInput,
  PostPreviewData,
  TaxonomyData,
} from "@/generated/api/src/models";
import { ApiError } from "@/lib/api";
import { SafeRenderedContent } from "@/features/blog/public/safe-rendered-content";
import { adminMediaApi, type AdminMediaApiBoundary } from "@/features/media/admin-api";
import { MediaPicker } from "@/features/media/media-picker";

import { adminBlogApi, type AdminBlogApiBoundary } from "./admin-api";
import styles from "./blog-admin.module.css";

type Draft = PostInput & { slug: string; visible: boolean };
const blank: Draft = {
  slug: "",
  title: "",
  excerpt: "",
  authorDisplay: "",
  source: "",
  seoTitle: "",
  seoDescription: "",
  canonicalUrl: "",
  tagIds: [],
  categoryIds: [],
  relatedPostIds: [],
  coverMediaId: null,
  visible: true,
};
const message = (error: unknown) =>
  error instanceof ApiError ? error.message : "The request could not be completed.";
const slugify = (value: string) =>
  value
    .normalize("NFKD")
    .toLowerCase()
    .replace(/[^a-z0-9]+/gu, "-")
    .replace(/^-|-$/gu, "");
const fromPost = (item: PostData): Draft => ({
  slug: item.slug,
  visible: item.visible,
  title: item.draft.title,
  excerpt: item.draft.excerpt,
  authorDisplay: item.draft.authorDisplay,
  source: item.draft.source,
  seoTitle: item.draft.seoTitle ?? "",
  seoDescription: item.draft.seoDescription ?? "",
  canonicalUrl: item.draft.canonicalUrl ?? "",
  tagIds: item.draft.tagIds ?? [],
  categoryIds: item.draft.categoryIds ?? [],
  relatedPostIds: item.draft.relatedPostIds ?? [],
  coverMediaId: item.draft.coverMediaId ?? null,
});
const inputOf = (draft: Draft): PostInput => ({
  title: draft.title,
  excerpt: draft.excerpt,
  authorDisplay: draft.authorDisplay,
  source: draft.source,
  tagIds: draft.tagIds ?? [],
  categoryIds: draft.categoryIds ?? [],
  relatedPostIds: draft.relatedPostIds ?? [],
  coverMediaId: draft.coverMediaId ?? null,
  seoTitle: draft.seoTitle || null,
  seoDescription: draft.seoDescription || null,
  canonicalUrl: draft.canonicalUrl || null,
});

export function BlogEditor({
  postId,
  api = adminBlogApi,
  mediaApi = adminMediaApi,
}: {
  postId?: string;
  api?: AdminBlogApiBoundary;
  mediaApi?: AdminMediaApiBoundary;
}) {
  const router = useRouter();
  const source = useRef<HTMLTextAreaElement>(null);
  const [item, setItem] = useState<PostData>();
  const [draft, setDraft] = useState<Draft>(blank);
  const [posts, setPosts] = useState<PostData[]>([]);
  const [tags, setTags] = useState<TaxonomyData[]>([]);
  const [categories, setCategories] = useState<TaxonomyData[]>([]);
  const [preview, setPreview] = useState<PostPreviewData>();
  const [tab, setTab] = useState<"write" | "preview">("write");
  const [publishAt, setPublishAt] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    void (async () => {
      try {
        if (postId) {
          const result = await api.get(postId);
          setItem(result.post);
          setDraft(fromPost(result.post));
          setPosts(result.posts);
          setTags(result.tags);
          setCategories(result.categories);
          if (result.post.publishAt && result.post.lifecycle === "scheduled")
            setPublishAt(result.post.publishAt.toISOString().slice(0, 16));
        } else {
          const result = await api.references();
          setPosts(result.posts);
          setTags(result.tags);
          setCategories(result.categories);
        }
      } catch (value) {
        setError(message(value));
      } finally {
        setLoading(false);
      }
    })();
  }, [api, postId]);

  async function persist(): Promise<PostData> {
    const saved = item
      ? await api.save(item, inputOf(draft))
      : await api.create({ ...inputOf(draft), slug: draft.slug, visible: draft.visible });
    setItem(saved);
    setDraft(fromPost(saved));
    if (!item) router.replace(`/admin/blog/${saved.id}/edit` as Route);
    return saved;
  }
  async function run(operation: () => Promise<void>, success: string) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await operation();
      setNotice(success);
    } catch (value) {
      setError(message(value));
    } finally {
      setBusy(false);
    }
  }
  async function save() {
    await run(async () => {
      await persist();
    }, "Draft saved. Reading time and checksum were recalculated by the server.");
  }
  async function showPreview() {
    await run(async () => {
      const saved = await persist();
      setPreview(await api.preview(saved.id));
      setTab("preview");
    }, "Preview refreshed from the saved draft.");
  }
  async function publish() {
    const publishingChanges = item?.lifecycle === "published_changes_pending";
    await run(
      async () => {
        const saved = await persist();
        const next = await api.publish(saved, publishAt ? new Date(publishAt) : undefined);
        setItem(next);
        setDraft(fromPost(next));
      },
      publishAt
        ? "Article scheduled."
        : publishingChanges
          ? "Pending changes published."
          : "Article published.",
    );
  }
  async function unpublish() {
    if (!item) return;
    await run(async () => {
      const next = await api.unpublish(item);
      setItem(next);
      setDraft(fromPost(next));
    }, "Article unpublished; its public route now returns not found.");
  }
  async function visibility() {
    if (!item) return;
    await run(
      async () => {
        const next = await api.setVisibility(item, !item.visible);
        setItem(next);
        setDraft(fromPost(next));
      },
      item.visible ? "Article hidden." : "Article visible.",
    );
  }
  async function remove() {
    if (!item || !window.confirm("Delete this article? Its public route will stop resolving."))
      return;
    await run(async () => {
      await api.delete(item);
      router.push("/admin/blog" as Route);
    }, "Article deleted.");
  }
  async function exportSource() {
    if (!item) return;
    await run(async () => {
      const data = await api.exportSource(item.id);
      const url = URL.createObjectURL(new Blob([data.source], { type: data.contentType }));
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = data.filename;
      anchor.click();
      URL.revokeObjectURL(url);
    }, "Exact normalized source exported.");
  }
  function insert(before: string, after = "") {
    const node = source.current;
    if (!node) return;
    const start = node.selectionStart;
    const end = node.selectionEnd;
    const next = `${draft.source.slice(0, start)}${before}${draft.source.slice(start, end)}${after}${draft.source.slice(end)}`;
    setDraft({ ...draft, source: next });
    requestAnimationFrame(() => {
      node.focus();
      node.setSelectionRange(start + before.length, end + before.length);
    });
  }
  function toggle(id: string, key: "tagIds" | "categoryIds" | "relatedPostIds") {
    const values = draft[key] ?? [];
    setDraft({
      ...draft,
      [key]: values.includes(id) ? values.filter((value) => value !== id) : [...values, id],
    });
  }
  if (loading) return <p className={styles.state}>Loading the editor…</p>;
  return (
    <div className={styles.editorPage}>
      <header className={styles.pageHeader}>
        <div>
          <Link href={"/admin/blog" as Route}>← Blog</Link>
          <p className="eyebrow">{item ? item.lifecycle.replaceAll("_", " ") : "New draft"}</p>
          <h1>{draft.title || "Untitled article"}</h1>
          <p>
            {item
              ? `Revision ${item.draft.revisionNumber} · ${item.draft.readingMinutes} min read · policy ${item.draft.contentPolicyName}@${item.draft.contentPolicyVersion}`
              : "Create a stable slug and first draft."}
          </p>
        </div>
        <div className={styles.headerActions}>
          <Button onClick={() => void showPreview()} variant="secondary" disabled={busy}>
            Preview
          </Button>
          {item ? (
            <Button onClick={() => void exportSource()} variant="quiet" disabled={busy}>
              Export source
            </Button>
          ) : null}
        </div>
      </header>
      {error ? (
        <p className={styles.error} role="alert">
          {error}
        </p>
      ) : null}
      {notice ? (
        <p className={styles.notice} role="status">
          {notice}
        </p>
      ) : null}
      <div className={styles.tabs} role="tablist" aria-label="Article editor">
        <Button
          aria-selected={tab === "write"}
          onClick={() => setTab("write")}
          role="tab"
          variant={tab === "write" ? "primary" : "quiet"}
        >
          Write
        </Button>
        <Button
          aria-selected={tab === "preview"}
          onClick={() => void showPreview()}
          role="tab"
          variant={tab === "preview" ? "primary" : "quiet"}
        >
          Preview
        </Button>
      </div>
      {tab === "preview" && preview ? (
        <section className={styles.preview} aria-label="Draft preview">
          <p className={styles.previewBanner}>{preview.banner}</p>
          <header>
            <p className="eyebrow">Private draft</p>
            <h2>{preview.title}</h2>
            <p>{preview.excerpt}</p>
            <small>
              {preview.authorDisplay} · {preview.readingMinutes} min read
            </small>
          </header>
          {preview.coverMediaId ? (
            // Authenticated draft media cannot use the public delivery route.
            // eslint-disable-next-line @next/next/no-img-element
            <img
              alt={`${preview.title} article cover`}
              className={styles.previewCover}
              src={`/api/v1/admin/media/${encodeURIComponent(preview.coverMediaId)}/content?width=1440&representation=webp`}
            />
          ) : null}
          <SafeRenderedContent content={preview.content} />
        </section>
      ) : (
        <div className={styles.editor}>
          <section>
            <h2>Identity</h2>
            <div className={styles.fields}>
              <label>
                Title
                <input
                  value={draft.title}
                  maxLength={160}
                  onChange={(event) =>
                    setDraft({
                      ...draft,
                      title: event.target.value,
                      ...(!item && !draft.slug ? { slug: slugify(event.target.value) } : {}),
                    })
                  }
                />
              </label>
              <label>
                Stable slug
                <input
                  value={draft.slug}
                  disabled={Boolean(item)}
                  pattern="[a-z0-9]+(?:-[a-z0-9]+)*"
                  onChange={(event) => setDraft({ ...draft, slug: event.target.value })}
                />
              </label>
              <label>
                Author
                <input
                  value={draft.authorDisplay}
                  maxLength={120}
                  onChange={(event) => setDraft({ ...draft, authorDisplay: event.target.value })}
                />
              </label>
              <label className={styles.wide}>
                Excerpt
                <textarea
                  rows={3}
                  value={draft.excerpt}
                  maxLength={500}
                  onChange={(event) => setDraft({ ...draft, excerpt: event.target.value })}
                />
              </label>
            </div>
          </section>
          <section>
            <div className={styles.sectionHeading}>
              <div>
                <h2>Article source</h2>
                <p>
                  Controlled CommonMark. Start sections with a level-one heading; the server demotes
                  headings beneath the article title. Raw HTML, images, embeds, unsafe links, and
                  unsupported code languages are rejected.
                </p>
              </div>
              <div className={styles.markdownToolbar} aria-label="Formatting toolbar">
                <Button onClick={() => insert("**", "**")} variant="quiet">
                  Bold
                </Button>
                <Button onClick={() => insert("## ")} variant="quiet">
                  Heading
                </Button>
                <Button onClick={() => insert("[", "](/path)")} variant="quiet">
                  Link
                </Button>
                <Button onClick={() => insert("```text\n", "\n```")} variant="quiet">
                  Code
                </Button>
              </div>
            </div>
            <label className={styles.sourceLabel}>
              <span className="sr-only">Article source</span>
              <textarea
                ref={source}
                rows={24}
                value={draft.source}
                onChange={(event) => setDraft({ ...draft, source: event.target.value })}
                spellCheck="true"
              />
            </label>
          </section>
          <section>
            <h2>Classification and relationships</h2>
            <div className={styles.pickers}>
              <Picker
                title="Categories"
                items={categories}
                selected={draft.categoryIds ?? []}
                onToggle={(id) => toggle(id, "categoryIds")}
              />
              <Picker
                title="Tags"
                items={tags}
                selected={draft.tagIds ?? []}
                onToggle={(id) => toggle(id, "tagIds")}
              />
              <Picker
                title="Related articles"
                items={posts.filter((value) => value.id !== item?.id)}
                selected={draft.relatedPostIds ?? []}
                onToggle={(id) => toggle(id, "relatedPostIds")}
                post
              />
            </div>
          </section>
          <section>
            <h2>Search and sharing</h2>
            <div className={styles.fields}>
              <label>
                SEO title
                <input
                  value={draft.seoTitle ?? ""}
                  maxLength={70}
                  onChange={(event) => setDraft({ ...draft, seoTitle: event.target.value })}
                />
              </label>
              <label>
                Canonical URL
                <input
                  type="url"
                  value={draft.canonicalUrl ?? ""}
                  placeholder="https://example.com/article"
                  onChange={(event) => setDraft({ ...draft, canonicalUrl: event.target.value })}
                />
              </label>
              <label className={styles.wide}>
                SEO description
                <textarea
                  rows={3}
                  value={draft.seoDescription ?? ""}
                  maxLength={180}
                  onChange={(event) => setDraft({ ...draft, seoDescription: event.target.value })}
                />
              </label>
            </div>
            <div className={styles.seoPreview}>
              <span>Search preview</span>
              <strong>{draft.seoTitle || draft.title || "Article title"}</strong>
              <p>{draft.seoDescription || draft.excerpt || "Article description"}</p>
            </div>
          </section>
          <section>
            <h2>Cover image</h2>
            <MediaPicker
              api={mediaApi}
              description="Used on the article card, public article header, and sharing metadata."
              disabled={busy}
              label="Article cover"
              onChange={(coverMediaId) => setDraft({ ...draft, coverMediaId })}
              value={draft.coverMediaId ?? null}
            />
          </section>
        </div>
      )}
      <section className={styles.lifecycle}>
        <div>
          <h2>Publication</h2>
          <p>Scheduling is evaluated against database time; no background worker is required.</p>
        </div>
        <div className={styles.lifecycleActions}>
          <label>
            Publish at (optional)
            <input
              type="datetime-local"
              value={publishAt}
              onChange={(event) => setPublishAt(event.target.value)}
            />
          </label>
          <Button disabled={busy} onClick={() => void publish()}>
            {publishAt
              ? "Schedule"
              : item?.lifecycle === "published_changes_pending"
                ? "Publish changes"
                : "Publish now"}
          </Button>
          {item &&
          ["published", "published_changes_pending", "scheduled"].includes(item.lifecycle) ? (
            <Button disabled={busy} onClick={() => void unpublish()} variant="secondary">
              Unpublish
            </Button>
          ) : null}
          {item ? (
            <Button disabled={busy} onClick={() => void visibility()} variant="quiet">
              {item.visible ? "Hide" : "Show"}
            </Button>
          ) : null}
          {item ? (
            <Button disabled={busy} onClick={() => void remove()} variant="danger">
              Delete
            </Button>
          ) : null}
        </div>
      </section>
      {tab === "write" ? (
        <div className={styles.saveBar}>
          <span>{item ? `Version ${item.version}` : "Unsaved first revision"}</span>
          <Button
            disabled={
              busy ||
              !draft.title ||
              !draft.slug ||
              !draft.authorDisplay ||
              !draft.excerpt ||
              !draft.source
            }
            onClick={() => void save()}
          >
            {busy ? "Working…" : "Save draft"}
          </Button>
        </div>
      ) : null}
    </div>
  );
}

function Picker({
  title,
  items,
  selected,
  onToggle,
  post = false,
}: {
  title: string;
  items: Array<TaxonomyData | PostData>;
  selected: string[];
  onToggle(id: string): void;
  post?: boolean;
}) {
  return (
    <fieldset>
      <legend>{title}</legend>
      {items.length ? (
        items.map((value) => (
          <label key={value.id}>
            <input
              type="checkbox"
              checked={selected.includes(value.id)}
              onChange={() => onToggle(value.id)}
            />
            <span>{post ? (value as PostData).draft.title : (value as TaxonomyData).name}</span>
          </label>
        ))
      ) : (
        <small>No options yet.</small>
      )}
    </fieldset>
  );
}

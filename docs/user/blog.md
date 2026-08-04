# Manage blog articles

The Blog workspace lets an administrator write controlled CommonMark source, preview the exact
server-rendered result privately, export the normalized source, and publish immediately or at a
future UTC instant. Later edits remain private until they are deliberately republished.

## Write and preview an article

1. Sign in and open **Content > Blog** at `/admin/blog`.
2. Choose **New article** and enter the title, stable slug, excerpt, author, and article source.
3. Optionally select tags, categories, related articles, and SEO title, description, and canonical
   URL. A cover image can be selected from the ready private media library.
4. Save the draft, then select **Preview**. Preview is authenticated, private, `no-store`, and
   excluded from indexing.
5. Use **Export source** to download the exact normalized `.md` source. Reload by pasting that
   source into an ordinary draft; no privileged filesystem import exists.

Slugs normalize to lowercase ASCII kebab-case and cannot be changed after creation. Reading time,
rendered HTML, checksum, and content-policy version are server-derived; they cannot be supplied or
overridden by the browser.

## Supported source and restrictions

Articles support headings, paragraphs, emphasis, named links, lists, block quotes, fenced and
inline code, tables, strikethrough, and read-only task lists. Start article sections with a source
`#` heading; the server places them below the page's article title.

Raw HTML, inline or remote images, embeds, iframes, objects, SVG, data URLs, unsafe URL schemes, and
runtime plug-ins are rejected. Use descriptive link text such as `About the architecture`, not
generic text such as `click here` or `read more`. Keep credentials, tokens, and private URLs out of
source and canonical links.

## Taxonomy and related articles

Tags and categories are stable reusable identities. They can be created and reordered from the
Blog workspace. A taxonomy still referenced by a retained draft or published revision cannot be
deleted. Related articles use stable post identities, reject duplicates and self-reference, and
show publicly only when the target is independently visible and published.

## Publication and recovery

- **Publish now** freezes the reviewed draft and creates a new editable copy in one transaction.
- A future publish time is stored as an absolute UTC instant and becomes eligible according to
  PostgreSQL time; no background worker changes status.
- Editing a published article produces **Published changes pending**. The public revision remains
  unchanged until **Publish changes** succeeds.
- **Reschedule** changes only the publication time. **Hide/Show** changes visibility independently.
- **Unpublish** removes the article from public list, detail, facets, metadata, JSON-LD, sitemap,
  and related summaries while retaining revisions. **Delete** is a separate soft-delete action.

Every mutation uses an ETag. If another session writes first, the stale request is rejected instead
of overwriting content. Reload the current server version, compare it with the retained source, and
reapply the intended change. Reuse an idempotency key only for the exact same create, publish,
reschedule, unpublish, or reorder request.

Visitors browse `/blog` and `/blog/{slug}`. Search, tag, category, order, and pagination are encoded
in the URL. Only visible, effective frozen publications contribute to results and totals; drafts,
future, hidden, unpublished, deleted, creator, revision, version, schedule, and policy internals are
never public.

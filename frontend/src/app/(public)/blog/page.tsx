import type { Metadata, Route } from "next";
import Link from "next/link";

import {
  PublicBlogPostsListSortEnum,
  type PublicBlogPostsListRequest,
} from "@/generated/api/src/apis/PublicBlogApi";
import { getPublicPosts } from "@/features/blog/public/public-api";
import { PostCard } from "@/features/blog/public/post-card";
import styles from "@/features/blog/public/blog.module.css";
import { publicMetadata } from "@/lib/discovery";

export const dynamic = "force-dynamic";
export const metadata: Metadata = publicMetadata({
  canonicalPath: "/blog",
  title: "Writing",
  description: "Notes on systems, craft, and useful software.",
});
type SearchParams = Promise<Record<string, string | string[] | undefined>>;
const one = (value: string | string[] | undefined) =>
  typeof value === "string" ? value : undefined;

function filtersFrom(
  params: Record<string, string | string[] | undefined>,
): PublicBlogPostsListRequest {
  const filters: PublicBlogPostsListRequest = {};
  const page = Number(one(params.page));
  if (Number.isSafeInteger(page) && page > 0) filters.page = page;
  for (const key of ["tag", "category", "search"] as const) {
    const value = one(params[key]);
    if (value) filters[key] = value;
  }
  const sort = one(params.sort);
  if (Object.values(PublicBlogPostsListSortEnum).includes(sort as never))
    filters.sort = sort as NonNullable<PublicBlogPostsListRequest["sort"]>;
  return filters;
}

function pageHref(params: Record<string, string | string[] | undefined>, page: number): Route {
  const query = new URLSearchParams();
  for (const key of ["tag", "category", "search", "sort"] as const) {
    const value = one(params[key]);
    if (value) query.set(key, value);
  }
  if (page > 1) query.set("page", String(page));
  return `/blog${query.size ? `?${query}` : ""}` as Route;
}

export default async function BlogPage({ searchParams }: { searchParams: SearchParams }) {
  const params = await searchParams;
  let result;
  try {
    result = await getPublicPosts(filtersFrom(params));
  } catch {
    return (
      <section className={styles.empty} role="alert">
        <p className="eyebrow">Writing</p>
        <h1>Articles are temporarily unavailable.</h1>
        <p>Try again shortly.</p>
      </section>
    );
  }
  return (
    <div>
      <header className={styles.hero}>
        <p className="eyebrow">Field notes</p>
        <h1>Ideas worth making useful.</h1>
        <p>
          Long-form notes on product engineering, dependable systems, and the decisions behind the
          work.
        </p>
        <form className={styles.filters} method="get">
          <label>
            Search
            <input defaultValue={one(params.search)} name="search" placeholder="Search articles" />
          </label>
          <label>
            Tag
            <input defaultValue={one(params.tag)} name="tag" placeholder="e.g. architecture" />
          </label>
          <label>
            Category
            <input
              defaultValue={one(params.category)}
              name="category"
              placeholder="e.g. engineering"
            />
          </label>
          <label>
            Order
            <select defaultValue={one(params.sort) ?? "newest"} name="sort">
              <option value="newest">Newest</option>
              <option value="oldest">Oldest</option>
              <option value="title">Title</option>
            </select>
          </label>
          <div className={styles.filterActions}>
            <button className="button button--primary" type="submit">
              Apply
            </button>
            <Link className="button button--quiet" href={"/blog" as Route}>
              Clear
            </Link>
          </div>
        </form>
      </header>
      <div className={styles.summary} aria-live="polite">
        <span>
          {result.meta.pagination.totalItems} published article
          {result.meta.pagination.totalItems === 1 ? "" : "s"}
        </span>
        <span>
          Page {result.meta.pagination.page} of {result.meta.pagination.totalPages || 1}
        </span>
      </div>
      {result.data.length ? (
        <>
          <ol className={styles.grid}>
            {result.data.map((item) => (
              <li key={item.id}>
                <PostCard item={item} />
              </li>
            ))}
          </ol>
          {result.meta.pagination.totalPages > 1 ? (
            <nav className={styles.pagination} aria-label="Article pages">
              {result.meta.pagination.hasPrevious ? (
                <Link href={pageHref(params, result.meta.pagination.page - 1)}>Previous</Link>
              ) : (
                <span aria-disabled="true">Previous</span>
              )}
              <span>
                Page {result.meta.pagination.page} of {result.meta.pagination.totalPages}
              </span>
              {result.meta.pagination.hasNext ? (
                <Link href={pageHref(params, result.meta.pagination.page + 1)}>Next</Link>
              ) : (
                <span aria-disabled="true">Next</span>
              )}
            </nav>
          ) : null}
        </>
      ) : (
        <section className={styles.empty} role="status">
          <p className="eyebrow">No matches</p>
          <h2>No published article matches these filters.</h2>
          <p>Clear the filters to browse the complete archive.</p>
        </section>
      )}
    </div>
  );
}

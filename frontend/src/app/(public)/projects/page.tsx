import type { Metadata, Route } from "next";
import Link from "next/link";

import {
  PublicProjectsListStatusEnum,
  type PublicProjectsListRequest,
} from "@/generated/api/src/apis/PublicProjectsApi";
import { getPublicProjects } from "@/features/projects/public/public-api";
import { ProjectCard } from "@/features/projects/public/project-card";
import styles from "@/features/projects/public/projects.module.css";
import { publicMetadata } from "@/lib/discovery";

export const dynamic = "force-dynamic";
export const metadata: Metadata = publicMetadata({
  canonicalPath: "/projects",
  title: "Projects",
  description: "Selected products, systems, and case studies.",
});
type SearchParams = Promise<Record<string, string | string[] | undefined>>;
const one = (value: string | string[] | undefined) =>
  typeof value === "string" ? value : undefined;

function filtersFrom(
  params: Record<string, string | string[] | undefined>,
): PublicProjectsListRequest {
  const filters: PublicProjectsListRequest = {};
  const page = Number(one(params.page));
  if (Number.isSafeInteger(page) && page > 0) filters.page = page;
  const status = one(params.status);
  if (Object.values(PublicProjectsListStatusEnum).includes(status as never))
    filters.status = status as NonNullable<PublicProjectsListRequest["status"]>;
  const search = one(params.search);
  if (search) filters.search = search;
  const technology = one(params.technology);
  if (technology) filters.technology = technology;
  return filters;
}

function pageHref(params: Record<string, string | string[] | undefined>, page: number): Route {
  const query = new URLSearchParams();
  for (const key of ["search", "status", "technology"] as const) {
    const value = one(params[key]);
    if (value) query.set(key, value);
  }
  if (page > 1) query.set("page", String(page));
  const encoded = query.toString();
  return `/projects${encoded ? `?${encoded}` : ""}` as Route;
}

export default async function ProjectsPage({ searchParams }: { searchParams: SearchParams }) {
  const params = await searchParams;
  let result;
  try {
    result = await getPublicProjects(filtersFrom(params));
  } catch {
    return (
      <section className={styles.empty} role="alert">
        <p className="eyebrow">Projects</p>
        <h1>Case studies are temporarily unavailable.</h1>
        <p>Try again shortly.</p>
      </section>
    );
  }
  return (
    <div>
      <header className={styles.hero}>
        <p className="eyebrow">Selected work</p>
        <h1>Systems with a point of view.</h1>
        <p>
          Products and platforms, unpacked through the problem, the decisions, and the measurable
          outcome.
        </p>
        <form className={styles.filters} method="get">
          <label>
            Search
            <input
              defaultValue={one(params.search)}
              name="search"
              placeholder="Search case studies"
            />
          </label>
          <label>
            Status
            <select defaultValue={one(params.status) ?? ""} name="status">
              <option value="">All statuses</option>
              {Object.entries(PublicProjectsListStatusEnum).map(([label, value]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Technology
            <input
              defaultValue={one(params.technology)}
              name="technology"
              placeholder="e.g. PostgreSQL"
            />
          </label>
          <div className={styles.actions}>
            <button className="button button--primary" type="submit">
              Apply
            </button>
            <Link className="button button--quiet" href={"/projects" as Route}>
              Clear
            </Link>
          </div>
        </form>
      </header>
      <div className={styles.resultSummary} aria-live="polite">
        <p>
          {result.meta.pagination.totalItems} published project
          {result.meta.pagination.totalItems === 1 ? "" : "s"}
        </p>
        {one(params.search) || one(params.status) || one(params.technology) ? (
          <p>Filters are active. Clear them to view the complete collection.</p>
        ) : (
          <p>Showing the complete published collection.</p>
        )}
      </div>
      {result.data.length ? (
        <>
          <h2 className={styles.resultsHeading} tabIndex={-1}>
            Project results
          </h2>
          <ol className={styles.grid}>
            {result.data.map((item, index) => (
              <li key={item.id}>
                <ProjectCard item={item} index={index} />
              </li>
            ))}
          </ol>
          {result.meta.pagination.totalPages > 1 ? (
            <nav className={styles.pagination} aria-label="Project pages">
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
          <h2>No published project matches these filters.</h2>
          <p>Clear the filters to explore all case studies.</p>
        </section>
      )}
    </div>
  );
}

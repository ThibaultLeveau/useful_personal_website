import type { Metadata, Route } from "next";
import Link from "next/link";

import { getPublicSkills, type PublicSkillFilters } from "@/features/skills/public-api";
import { PublicSkills } from "@/features/skills/public-skills";
import styles from "@/features/skills/skills.module.css";
import { publicMetadata } from "@/lib/discovery";

export const metadata: Metadata = publicMetadata({
  canonicalPath: "/skills",
  title: "Skills",
  description: "A grouped, filterable view of published skills and experience.",
});

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

function one(value: string | string[] | undefined): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function filtersFrom(params: Record<string, string | string[] | undefined>): PublicSkillFilters {
  const category = one(params.category);
  const search = one(params.search);
  const featured = one(params.featured);
  return {
    ...(category ? { category } : {}),
    ...(search ? { search } : {}),
    ...(featured === "true" ? { featured: true } : {}),
  };
}

export default async function SkillsPage({ searchParams }: { searchParams: SearchParams }) {
  const params = await searchParams;
  const filters = filtersFrom(params);
  let catalog;
  let result;
  try {
    [catalog, result] = await Promise.all([getPublicSkills(), getPublicSkills(filters)]);
  } catch {
    return (
      <div>
        <section className={styles.empty} role="alert">
          <p className="eyebrow">Skills</p>
          <h1>The skills catalog is temporarily unavailable.</h1>
          <p>Try again shortly.</p>
        </section>
      </div>
    );
  }
  const categories = [...new Map(catalog.data.map((item) => [item.categorySlug, item])).values()];
  return (
    <div>
      <header className={styles.hero}>
        <p className="eyebrow">Capability map</p>
        <h1>Skills, grounded in practice.</h1>
        <p>
          Browse published capabilities by discipline, focus on featured work, or search the
          catalog. Private and draft entries never reach this page.
        </p>
        <form className={styles.filters} method="get" role="search">
          <label>
            Search skills
            <input defaultValue={one(params.search)} maxLength={120} name="search" type="search" />
          </label>
          <label>
            Category
            <select defaultValue={one(params.category) ?? ""} name="category">
              <option value="">All categories</option>
              {categories.map((category) => (
                <option key={category.categorySlug} value={category.categorySlug}>
                  {category.categoryName}
                </option>
              ))}
            </select>
          </label>
          <label>
            Focus
            <select defaultValue={one(params.featured) ?? ""} name="featured">
              <option value="">All skills</option>
              <option value="true">Featured only</option>
            </select>
          </label>
          <div className={styles.filterActions}>
            <button className="button button--primary" type="submit">
              Apply
            </button>
            <Link className="button button--quiet" href={"/skills" as Route}>
              Clear
            </Link>
          </div>
        </form>
      </header>
      <PublicSkills skills={result.data} />
    </div>
  );
}

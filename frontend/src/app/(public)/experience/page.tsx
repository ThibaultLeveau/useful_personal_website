import type { Metadata, Route } from "next";
import Link from "next/link";

import {
  PublicExperiencesListEmploymentTypeEnum,
  PublicExperiencesListRemoteStatusEnum,
  type PublicExperiencesListRequest,
} from "@/generated/api/src/apis/PublicExperiencesApi";
import { ExperienceTimeline } from "@/features/experiences/public/experience-timeline";
import styles from "@/features/experiences/public/experiences.module.css";
import { getPublicExperiences } from "@/features/experiences/public/public-api";
import { publicMetadata } from "@/lib/discovery";

export const dynamic = "force-dynamic";

export const metadata: Metadata = publicMetadata({
  canonicalPath: "/experience",
  title: "Experience",
  description: "A chronological record of professional work, outcomes, and capabilities.",
});

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

function one(value: string | string[] | undefined): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function filtersFrom(params: Record<string, string | string[] | undefined>) {
  const current = one(params.current);
  const employmentType = one(params.employment_type);
  const remoteStatus = one(params.remote_status);
  const filters: PublicExperiencesListRequest = {};
  if (current === "true") filters.current = true;
  if (Object.values(PublicExperiencesListEmploymentTypeEnum).includes(employmentType as never)) {
    filters.employmentType = employmentType as NonNullable<
      PublicExperiencesListRequest["employmentType"]
    >;
  }
  if (Object.values(PublicExperiencesListRemoteStatusEnum).includes(remoteStatus as never)) {
    filters.remoteStatus = remoteStatus as NonNullable<
      PublicExperiencesListRequest["remoteStatus"]
    >;
  }
  return filters;
}

export default async function ExperiencePage({ searchParams }: { searchParams: SearchParams }) {
  const params = await searchParams;
  let result;
  try {
    result = await getPublicExperiences(filtersFrom(params));
  } catch {
    return (
      <section className={styles.empty} role="alert">
        <p className="eyebrow">Experience</p>
        <h1>The experience timeline is temporarily unavailable.</h1>
        <p>Try again shortly.</p>
      </section>
    );
  }

  return (
    <div>
      <header className={styles.hero}>
        <p className="eyebrow">Professional record</p>
        <h1>Work, in context.</h1>
        <p>
          A chronological account of roles, responsibilities, and outcomes—connected to the
          capabilities used to deliver them.
        </p>
        <form className={styles.filters} method="get">
          <label>
            Status
            <select defaultValue={one(params.current) ?? ""} name="current">
              <option value="">All roles</option>
              <option value="true">Current roles</option>
            </select>
          </label>
          <label>
            Engagement
            <select defaultValue={one(params.employment_type) ?? ""} name="employment_type">
              <option value="">All engagements</option>
              {Object.entries(PublicExperiencesListEmploymentTypeEnum).map(([label, value]) => (
                <option key={value} value={value}>
                  {label.replace(/([a-z])([A-Z])/gu, "$1 $2")}
                </option>
              ))}
            </select>
          </label>
          <label>
            Work style
            <select defaultValue={one(params.remote_status) ?? ""} name="remote_status">
              <option value="">All arrangements</option>
              {Object.entries(PublicExperiencesListRemoteStatusEnum).map(([label, value]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <div className={styles.filterActions}>
            <button className="button button--primary" type="submit">
              Apply
            </button>
            <Link className="button button--quiet" href={"/experience" as Route}>
              Clear
            </Link>
          </div>
        </form>
      </header>
      <ExperienceTimeline experiences={result.data} />
    </div>
  );
}

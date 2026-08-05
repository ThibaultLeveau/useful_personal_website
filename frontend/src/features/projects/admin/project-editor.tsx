"use client";

import type { Route } from "next";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";

import { ProjectStatus } from "@/generated/api/src/models/ProjectStatus";
import type { ProjectCreateRequest, ProjectData, ProjectInput } from "@/generated/api/src/models";
import { ApiError } from "@/lib/api";
import { zonedLocalToUtc } from "@/features/experiences/admin/timezone";
import { adminMediaApi, type AdminMediaApiBoundary } from "@/features/media/admin-api";
import { MediaPicker } from "@/features/media/media-picker";

import {
  adminProjectsApi,
  type AdminProjectsApiBoundary,
  type ProjectReferenceSnapshot,
} from "./admin-api";
import styles from "./projects-admin.module.css";

const EMPTY: ProjectInput = {
  architecture: "Describe the system architecture.",
  canonicalUrl: null,
  coverMediaId: null,
  demoUrl: null,
  endDate: null,
  experienceIds: [],
  fullDescription: "## Overview\n\nDescribe the project.",
  impact: "Describe the measured impact.",
  name: "",
  ownerRole: "",
  problem: "Describe the problem.",
  relatedProjectIds: [],
  repositoryUrl: null,
  screenshotMediaIds: [],
  seoDescription: null,
  seoTitle: null,
  shortDescription: "",
  skillIds: [],
  solution: "Describe the solution.",
  startDate: new Date(),
  status: ProjectStatus.Active,
  technologies: ["TypeScript"],
};

function dateValue(value: Date | null) {
  return value ? value.toISOString().slice(0, 10) : "";
}
function optional(value: FormDataEntryValue | null) {
  const text = String(value ?? "").trim();
  return text || null;
}
function values(
  form: HTMLFormElement,
  coverMediaId: string | null,
  screenshotMediaIds: string[],
): ProjectInput {
  const data = new FormData(form);
  return {
    name: String(data.get("name") ?? ""),
    shortDescription: String(data.get("shortDescription") ?? ""),
    fullDescription: String(data.get("fullDescription") ?? ""),
    problem: String(data.get("problem") ?? ""),
    solution: String(data.get("solution") ?? ""),
    impact: String(data.get("impact") ?? ""),
    ownerRole: String(data.get("ownerRole") ?? ""),
    architecture: String(data.get("architecture") ?? ""),
    technologies: String(data.get("technologies") ?? "")
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean),
    status: String(data.get("status")) as ProjectInput["status"],
    startDate: new Date(`${String(data.get("startDate"))}T00:00:00Z`),
    endDate: data.get("endDate") ? new Date(`${String(data.get("endDate"))}T00:00:00Z`) : null,
    repositoryUrl: optional(data.get("repositoryUrl")),
    demoUrl: optional(data.get("demoUrl")),
    skillIds: data.getAll("skillIds").map(String),
    experienceIds: data.getAll("experienceIds").map(String),
    relatedProjectIds: data.getAll("relatedProjectIds").map(String),
    seoTitle: optional(data.get("seoTitle")),
    seoDescription: optional(data.get("seoDescription")),
    canonicalUrl: optional(data.get("canonicalUrl")),
    coverMediaId,
    screenshotMediaIds,
  };
}

export function ProjectEditor({
  api = adminProjectsApi,
  mediaApi = adminMediaApi,
  projectId,
}: {
  api?: AdminProjectsApiBoundary;
  mediaApi?: AdminMediaApiBoundary;
  projectId?: string;
}) {
  const router = useRouter();
  const [project, setProject] = useState<ProjectData | null>(null);
  const [references, setReferences] = useState<ProjectReferenceSnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [schedule, setSchedule] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [coverMediaId, setCoverMediaId] = useState<string | null>(null);
  const [screenshotMediaIds, setScreenshotMediaIds] = useState<string[]>([]);

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        if (projectId) {
          const result = await api.get(projectId);
          if (!active) return;
          setProject(result.project);
          setReferences(result);
          setCoverMediaId(result.project.draft.coverMediaId ?? null);
          setScreenshotMediaIds(result.project.draft.screenshotMediaIds ?? []);
        } else {
          const result = await api.references();
          if (!active) return;
          setReferences(result);
        }
      } catch (cause) {
        if (active)
          setError(cause instanceof ApiError ? cause.message : "The editor could not be loaded.");
      }
    })();
    return () => {
      active = false;
    };
  }, [api, projectId]);

  const initial: ProjectInput = project
    ? {
        ...project.draft,
        canonicalUrl: project.draft.canonicalUrl ?? null,
        coverMediaId: project.draft.coverMediaId ?? null,
        demoUrl: project.draft.demoUrl ?? null,
        endDate: project.draft.endDate ?? null,
        experienceIds: project.draft.experienceIds ?? [],
        relatedProjectIds: project.draft.relatedProjectIds ?? [],
        repositoryUrl: project.draft.repositoryUrl ?? null,
        screenshotMediaIds: project.draft.screenshotMediaIds ?? [],
        seoDescription: project.draft.seoDescription ?? null,
        seoTitle: project.draft.seoTitle ?? null,
        skillIds: project.draft.skillIds ?? [],
      }
    : EMPTY;
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      const input = values(event.currentTarget, coverMediaId, screenshotMediaIds);
      if (project) {
        const result = await api.save(project, input);
        setProject(result);
        setNotice("Project saved");
      } else {
        const result = await api.create({
          ...input,
          slug: String(new FormData(event.currentTarget).get("slug") ?? ""),
          visible: true,
          featured: false,
        } satisfies ProjectCreateRequest);
        router.push(`/admin/projects/${result.id}/edit` as Route);
      }
      router.refresh();
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "The project could not be saved.");
    } finally {
      setSaving(false);
    }
  }
  async function action(operation: (item: ProjectData) => Promise<ProjectData>, success: string) {
    if (!project) return;
    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      setProject(await operation(project));
      setNotice(success);
    } catch (cause) {
      setError(
        cause instanceof ApiError ? cause.message : "The lifecycle action could not be completed.",
      );
    } finally {
      setSaving(false);
    }
  }
  if (!references && !error)
    return (
      <section className={styles.state} role="status">
        Loading the project editor…
      </section>
    );
  return (
    <div className={styles.editorPage}>
      <header className={styles.pageHeader}>
        <div>
          <p className="eyebrow">Projects / {project ? "Edit" : "Create"}</p>
          <h1>{project?.draft.name || "New case study"}</h1>
          <p>
            {project
              ? `Stable route: /projects/${project.slug}`
              : "Create the stable route and first editable draft."}
          </p>
        </div>
        <div className={styles.headerActions}>
          <Link className="button button--quiet" href={"/admin/projects" as Route}>
            Back
          </Link>
          {project ? (
            <Link
              className="button button--secondary"
              href={`/admin/projects/${project.id}/preview` as Route}
            >
              Preview
            </Link>
          ) : null}
        </div>
      </header>
      {error ? (
        <div className={styles.error} role="alert">
          <strong>Review required</strong>
          <p>{error}</p>
        </div>
      ) : null}
      {notice ? (
        <p className={styles.notice} role="status">
          {notice}
        </p>
      ) : null}
      {project ? (
        <section className={styles.lifecycle} aria-labelledby="project-lifecycle">
          <div>
            <p className="eyebrow">Lifecycle</p>
            <h2 id="project-lifecycle">{project.lifecycle.replaceAll("_", " ")}</h2>
            <p>Visibility and featured placement remain independent from publication.</p>
          </div>
          <div className={styles.lifecycleActions}>
            <button
              className="button button--quiet"
              disabled={saving}
              onClick={() =>
                void action(
                  (item) => api.setVisibility(item, !item.visible),
                  project.visible ? "Project hidden" : "Project visible",
                )
              }
              type="button"
            >
              {project.visible ? "Hide" : "Show"}
            </button>
            <button
              className="button button--quiet"
              disabled={saving}
              onClick={() =>
                void action(
                  (item) => api.setFeatured(item, !item.featured),
                  project.featured ? "Project removed from featured work" : "Project featured",
                )
              }
              type="button"
            >
              {project.featured ? "Unfeature" : "Feature"}
            </button>
            {project.published ? (
              <>
                {project.lifecycle === "published_changes_pending" ? (
                  <button
                    className="button button--primary"
                    disabled={saving}
                    onClick={() =>
                      void action((item) => api.publish(item), "Pending changes published")
                    }
                    type="button"
                  >
                    Publish changes
                  </button>
                ) : null}
                <button
                  className="button button--quiet"
                  disabled={saving}
                  onClick={() => void action((item) => api.unpublish(item), "Project unpublished")}
                  type="button"
                >
                  Unpublish
                </button>
              </>
            ) : (
              <button
                className="button button--primary"
                disabled={saving}
                onClick={() => void action((item) => api.publish(item), "Project published")}
                type="button"
              >
                Publish now
              </button>
            )}
            <label>
              Schedule in {references?.timezone}
              <input
                type="datetime-local"
                value={schedule}
                onChange={(event) => setSchedule(event.target.value)}
              />
            </label>
            <button
              className="button button--secondary"
              disabled={saving || !schedule}
              onClick={() => {
                if (!references) return;
                void action(
                  (item) =>
                    project.published
                      ? api.reschedule(item, zonedLocalToUtc(schedule, references.timezone))
                      : api.publish(item, zonedLocalToUtc(schedule, references.timezone)),
                  project.published ? "Publication rescheduled" : "Publication scheduled",
                );
              }}
              type="button"
            >
              {project.published ? "Reschedule" : "Schedule"}
            </button>
            <label className={styles.confirm}>
              <input
                checked={confirmDelete}
                onChange={(event) => setConfirmDelete(event.target.checked)}
                type="checkbox"
              />
              Confirm deletion
            </label>
            <button
              className="button button--danger"
              disabled={saving || !confirmDelete}
              onClick={() =>
                void (async () => {
                  try {
                    await api.delete(project);
                    router.push("/admin/projects" as Route);
                  } catch (cause) {
                    setError(
                      cause instanceof ApiError
                        ? cause.message
                        : "The project could not be deleted.",
                    );
                  }
                })()
              }
              type="button"
            >
              Delete
            </button>
          </div>
        </section>
      ) : null}
      <form className={styles.editor} onSubmit={submit}>
        <section>
          <h2>Identity and summary</h2>
          <div className={styles.fields}>
            {!project ? (
              <label>
                Slug
                <input defaultValue="" name="slug" required placeholder="api-platform" />
              </label>
            ) : null}
            <label>
              Project name
              <input defaultValue={initial.name} name="name" maxLength={180} required />
            </label>
            <label className={styles.wide}>
              Short description
              <textarea
                defaultValue={initial.shortDescription}
                name="shortDescription"
                maxLength={500}
                required
                rows={3}
              />
            </label>
            <label>
              Owner role
              <input defaultValue={initial.ownerRole} name="ownerRole" maxLength={180} required />
            </label>
            <label>
              Status
              <select defaultValue={initial.status} name="status">
                {Object.values(ProjectStatus).map((value) => (
                  <option value={value} key={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Start date
              <input
                defaultValue={dateValue(initial.startDate)}
                name="startDate"
                required
                type="date"
              />
            </label>
            <label>
              End date
              <input defaultValue={dateValue(initial.endDate ?? null)} name="endDate" type="date" />
            </label>
          </div>
        </section>
        <section>
          <h2>Case study</h2>
          <p className={styles.hint}>
            Controlled Markdown supports headings, lists, and safe links. Raw HTML is rejected.
          </p>
          <div className={styles.fields}>
            {(
              [
                ["fullDescription", "Overview", initial.fullDescription],
                ["problem", "Problem", initial.problem],
                ["solution", "Solution", initial.solution],
                ["architecture", "Architecture", initial.architecture],
                ["impact", "Impact", initial.impact],
              ] as const
            ).map(([name, label, value]) => (
              <label className={styles.wide} key={name}>
                {label}
                <textarea defaultValue={value} name={name} required rows={7} />
              </label>
            ))}
          </div>
        </section>
        <section>
          <h2>Technology and links</h2>
          <div className={styles.fields}>
            <label className={styles.wide}>
              Technologies, comma-separated
              <input defaultValue={initial.technologies.join(", ")} name="technologies" required />
            </label>
            <label>
              Repository URL
              <input
                defaultValue={initial.repositoryUrl ?? ""}
                name="repositoryUrl"
                type="url"
                placeholder="https://"
              />
            </label>
            <label>
              Demo URL
              <input
                defaultValue={initial.demoUrl ?? ""}
                name="demoUrl"
                type="url"
                placeholder="https://"
              />
            </label>
          </div>
        </section>
        <section>
          <h2>Evidence and relationships</h2>
          <div className={styles.pickers}>
            <fieldset>
              <legend>Skills</legend>
              {references?.skills.map((item) => (
                <label key={item.id}>
                  <input
                    defaultChecked={(initial.skillIds ?? []).includes(item.id)}
                    name="skillIds"
                    type="checkbox"
                    value={item.id}
                  />
                  {item.name}
                </label>
              ))}
            </fieldset>
            <fieldset>
              <legend>Experience</legend>
              {references?.experiences.map((item) => (
                <label key={item.id}>
                  <input
                    defaultChecked={(initial.experienceIds ?? []).includes(item.id)}
                    name="experienceIds"
                    type="checkbox"
                    value={item.id}
                  />
                  {item.draft.roleTitle} · {item.draft.companyName}
                </label>
              ))}
            </fieldset>
            <fieldset>
              <legend>Related projects</legend>
              {references?.projects
                .filter((item) => item.id !== project?.id)
                .map((item) => (
                  <label key={item.id}>
                    <input
                      defaultChecked={(initial.relatedProjectIds ?? []).includes(item.id)}
                      name="relatedProjectIds"
                      type="checkbox"
                      value={item.id}
                    />
                    {item.draft.name}
                    <small>{item.lifecycle}</small>
                  </label>
                ))}
            </fieldset>
          </div>
        </section>
        <section>
          <h2>Search presentation</h2>
          <div className={styles.fields}>
            <label>
              SEO title
              <input defaultValue={initial.seoTitle ?? ""} maxLength={70} name="seoTitle" />
            </label>
            <label className={styles.wide}>
              SEO description
              <textarea
                defaultValue={initial.seoDescription ?? ""}
                maxLength={180}
                name="seoDescription"
                rows={3}
              />
            </label>
            <label className={styles.wide}>
              Canonical URL
              <input
                defaultValue={initial.canonicalUrl ?? ""}
                name="canonicalUrl"
                type="url"
                placeholder="https://"
              />
            </label>
          </div>
          <div className={styles.seoPreview}>
            <span>Search preview</span>
            <strong>{initial.seoTitle || initial.name || "Project title"}</strong>
            <p>{initial.seoDescription || initial.shortDescription || "Project description"}</p>
          </div>
        </section>
        <section>
          <h2>Media</h2>
          <div className={styles.mediaFields}>
            <MediaPicker
              api={mediaApi}
              description="Used on project cards and at the top of the published case study."
              disabled={saving}
              label="Project cover"
              onChange={(assetId) => {
                setCoverMediaId(assetId);
                if (assetId) {
                  setScreenshotMediaIds((current) =>
                    current.filter((identifier) => identifier !== assetId),
                  );
                }
              }}
              value={coverMediaId}
            />
            <div className={styles.screenshotPickers}>
              <div>
                <h3>Screenshot gallery</h3>
                <p>Images remain in this order on the published project page.</p>
              </div>
              {screenshotMediaIds.map((assetId, index) => (
                <MediaPicker
                  api={mediaApi}
                  description={`Gallery position ${index + 1}. Clear it to remove this image.`}
                  disabled={saving}
                  key={`${assetId}-${index}`}
                  label={`Screenshot ${index + 1}`}
                  onChange={(nextId) => {
                    setScreenshotMediaIds((current) => {
                      if (!nextId) return current.filter((_, position) => position !== index);
                      if (nextId === coverMediaId) {
                        setError("The project cover cannot also be a screenshot.");
                        return current;
                      }
                      if (
                        current.some(
                          (identifier, position) => identifier === nextId && position !== index,
                        )
                      ) {
                        setError("Each screenshot can appear only once.");
                        return current;
                      }
                      return current.map((identifier, position) =>
                        position === index ? nextId : identifier,
                      );
                    });
                  }}
                  value={assetId}
                />
              ))}
              <MediaPicker
                api={mediaApi}
                description="Choose another ready image from the private media library."
                disabled={saving}
                label="Add screenshot"
                onChange={(assetId) => {
                  if (!assetId) return;
                  if (assetId === coverMediaId) {
                    setError("The project cover cannot also be a screenshot.");
                    return;
                  }
                  setScreenshotMediaIds((current) =>
                    current.includes(assetId) ? current : [...current, assetId],
                  );
                }}
                value={null}
              />
            </div>
          </div>
        </section>
        <footer className={styles.saveBar}>
          <span>{project ? `Version ${project.version} · ${project.lifecycle}` : "New draft"}</span>
          <button className="button button--primary" disabled={saving} type="submit">
            {saving ? "Saving…" : "Save project"}
          </button>
        </footer>
      </form>
    </div>
  );
}

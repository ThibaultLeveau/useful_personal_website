"use client";

import type { Route } from "next";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { LoadingPanel } from "@/components/ui/loading-panel";
import type {
  EmploymentType,
  ExperienceData,
  ExperienceInput,
  ExperienceRevisionData,
  RemoteStatus,
  SkillData,
} from "@/generated/api/src/models";
import { useAuth } from "@/features/auth/auth-context";
import {
  FormStatus,
  UnsavedChangesGuard,
  toApiError,
  useDeferredInitialLoad,
} from "@/features/site-configuration/configuration-form";
import { ApiError } from "@/lib/api";

import { adminExperiencesApi, type AdminExperiencesApiBoundary } from "./admin-api";
import styles from "./experiences-admin.module.css";
import { formatInTimezone, zonedLocalToUtc } from "./timezone";

type EditorTab = "content" | "publication" | "relations";

const employmentOptions: Array<[EmploymentType, string]> = [
  ["full_time", "Full time"],
  ["part_time", "Part time"],
  ["contract", "Contract"],
  ["freelance", "Freelance"],
  ["internship", "Internship"],
  ["apprenticeship", "Apprenticeship"],
  ["temporary", "Temporary"],
  ["seasonal", "Seasonal"],
  ["volunteer", "Volunteer"],
];

const remoteOptions: Array<[RemoteStatus, string]> = [
  ["onsite", "On-site"],
  ["hybrid", "Hybrid"],
  ["remote", "Remote"],
];

function calendarValue(date: Date | null | undefined): string {
  return date?.toISOString().slice(0, 10) ?? "";
}

function calendarDate(value: string): Date {
  return new Date(`${value}T00:00:00.000Z`);
}

function mutableInput(revision: ExperienceRevisionData): ExperienceInput {
  return {
    achievements: [...(revision.achievements ?? [])],
    companyName: revision.companyName,
    companyUrl: revision.companyUrl ?? null,
    currentPosition: revision.currentPosition,
    detailedDescription: revision.detailedDescription ?? null,
    employmentType: revision.employmentType,
    endDate: revision.endDate ?? null,
    location: revision.location ?? null,
    remoteStatus: revision.remoteStatus,
    responsibilities: [...(revision.responsibilities ?? [])],
    roleTitle: revision.roleTitle,
    shortSummary: revision.shortSummary,
    skillIds: [...(revision.skillIds ?? [])],
    startDate: revision.startDate,
    technologies: [...(revision.technologies ?? [])],
  };
}

function validate(input: ExperienceInput): Record<string, string> {
  const errors: Record<string, string> = {};
  if (!input.companyName.trim()) errors.companyName = "Enter a company name.";
  if (!input.roleTitle.trim()) errors.roleTitle = "Enter a role title.";
  if (!input.shortSummary.trim()) errors.shortSummary = "Enter a short summary.";
  if (Number.isNaN(input.startDate.getTime())) errors.startDate = "Enter a valid start date.";
  if (input.currentPosition && input.endDate) {
    errors.endDate = "A current position cannot have an end date.";
  } else if (input.endDate && input.endDate < input.startDate) {
    errors.endDate = "End date must be on or after the start date.";
  }
  return errors;
}

function FieldError({ error, id }: { error: string | undefined; id: string }) {
  return error ? (
    <span className={styles.fieldError} id={id}>
      {error}
    </span>
  ) : null;
}

function OrderedField({
  label,
  onChange,
  values,
}: {
  label: string;
  onChange: (values: string[]) => void;
  values: string[];
}) {
  function move(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= values.length) return;
    const next = [...values];
    [next[index], next[target]] = [next[target] as string, next[index] as string];
    onChange(next);
  }

  return (
    <fieldset className={styles.orderedField}>
      <legend>{label}</legend>
      <ol className={styles.orderedList}>
        {values.map((item, index) => (
          <li className={styles.orderedItem} key={`${label}-${index}`}>
            <label>
              <span className="visually-hidden">
                {label} item {index + 1}
              </span>
              <input
                maxLength={1000}
                onChange={(event) =>
                  onChange(
                    values.map((value, itemIndex) =>
                      itemIndex === index ? event.target.value : value,
                    ),
                  )
                }
                value={item}
              />
            </label>
            <div className={styles.orderedActions}>
              <Button
                aria-label={`Move ${label} item ${index + 1} up`}
                disabled={index === 0}
                onClick={() => move(index, -1)}
                variant="quiet"
              >
                ↑
              </Button>
              <Button
                aria-label={`Move ${label} item ${index + 1} down`}
                disabled={index === values.length - 1}
                onClick={() => move(index, 1)}
                variant="quiet"
              >
                ↓
              </Button>
              <Button
                aria-label={`Remove ${label} item ${index + 1}`}
                onClick={() => onChange(values.filter((_, itemIndex) => itemIndex !== index))}
                variant="danger"
              >
                Remove
              </Button>
            </div>
          </li>
        ))}
      </ol>
      <Button onClick={() => onChange([...values, ""])} variant="secondary">
        Add {label.toLowerCase()} item
      </Button>
    </fieldset>
  );
}

export function ExperienceEditor({
  api = adminExperiencesApi,
  experienceId,
}: {
  api?: AdminExperiencesApiBoundary;
  experienceId: string;
}) {
  const auth = useAuth();
  const summary = useRef<HTMLDivElement>(null);
  const [item, setItem] = useState<ExperienceData | null>(null);
  const [input, setInput] = useState<ExperienceInput | null>(null);
  const [skills, setSkills] = useState<SkillData[]>([]);
  const [timezone, setTimezone] = useState("UTC");
  const [tab, setTab] = useState<EditorTab>("content");
  const [schedule, setSchedule] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [apiError, setApiError] = useState<ApiError | null>(null);
  const [saved, setSaved] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [dirty, setDirty] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setApiError(null);
    try {
      const snapshot = await api.get(experienceId);
      setItem(snapshot.experience);
      setInput(mutableInput(snapshot.experience.draft));
      setSkills(snapshot.skills);
      setTimezone(snapshot.timezone);
      setDirty(false);
    } catch (caught) {
      const next = toApiError(caught);
      setApiError(next);
      if (next.status === 401) auth.expireSession();
    } finally {
      setLoading(false);
    }
  }, [api, auth, experienceId]);

  useDeferredInitialLoad(load);

  useEffect(() => {
    if (Object.keys(errors).length) summary.current?.focus();
  }, [errors]);

  function change(patch: Partial<ExperienceInput>) {
    setInput((current) => (current ? { ...current, ...patch } : current));
    setDirty(true);
    setSaved(null);
  }

  async function run(action: () => Promise<ExperienceData>, message: string): Promise<boolean> {
    setBusy(true);
    setApiError(null);
    setSaved(null);
    try {
      const updated = await action();
      setItem(updated);
      setInput(mutableInput(updated.draft));
      setDirty(false);
      setSaved(message);
      return true;
    } catch (caught) {
      const next = toApiError(caught);
      setApiError(next);
      if (next.status === 401) auth.expireSession();
      return false;
    } finally {
      setBusy(false);
    }
  }

  async function save(): Promise<boolean> {
    if (!item || !input) return false;
    const localErrors = validate(input);
    setErrors(localErrors);
    if (Object.keys(localErrors).length) {
      const first = Object.keys(localErrors)[0];
      if (
        first &&
        ["companyName", "roleTitle", "shortSummary", "startDate", "endDate"].includes(first)
      ) {
        setTab("content");
      }
      return false;
    }
    return run(() => api.save(item, input), "Draft saved.");
  }

  if (loading) return <LoadingPanel label="Loading experience editor" />;
  if (!item || !input) {
    return (
      <div className={styles.empty} role="alert">
        <h1>Experience unavailable</h1>
        <p>{apiError?.message ?? "The requested draft could not be loaded."}</p>
      </div>
    );
  }

  const hiddenSelections = skills.filter(
    (skill) => input.skillIds?.includes(skill.id) && !skill.visible,
  );
  const localErrors = Object.keys(errors).length;

  return (
    <div className={styles.editor}>
      <UnsavedChangesGuard dirty={dirty} onSave={save} />
      <header className={styles.pageHeader}>
        <div>
          <p className="eyebrow">Experience / Draft editor</p>
          <h1>{input.roleTitle || "Untitled role"}</h1>
          <div className={styles.statusCluster}>
            <span className={styles.status} data-state={item.lifecycle}>
              <i aria-hidden="true" />
              {item.lifecycle.replaceAll("_", " ")}
            </span>
            <span className={styles.visibility}>{item.visible ? "◆ Visible" : "◇ Hidden"}</span>
          </div>
        </div>
        <div className={styles.editorActions}>
          {item.published ? (
            <Link className="button button--quiet" href={"/experience" as Route}>
              View live
            </Link>
          ) : null}
          <Link
            className="button button--secondary"
            href={`/admin/experiences/${item.id}/preview` as Route}
          >
            Preview draft
          </Link>
          <Button disabled={busy} onClick={() => void save()}>
            {busy ? "Saving…" : "Save draft"}
          </Button>
        </div>
      </header>

      <FormStatus error={apiError} saved={saved} />
      {apiError?.code === "RESOURCE_VERSION_CONFLICT" ? (
        <div className={styles.conflictActions}>
          <Button onClick={() => void load()} variant="secondary">
            Review latest version
          </Button>
          <Button
            onClick={() => void navigator.clipboard.writeText(JSON.stringify(input, null, 2))}
            variant="quiet"
          >
            Copy my changes
          </Button>
        </div>
      ) : null}
      {localErrors ? (
        <div className={styles.errorSummary} ref={summary} role="alert" tabIndex={-1}>
          <h2>
            Fix {localErrors} field {localErrors === 1 ? "error" : "errors"}
          </h2>
          <ul>
            {Object.entries(errors).map(([field, message]) => (
              <li key={field}>
                <a href={`#${field}`}>{message}</a>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className={styles.tabs} role="tablist" aria-label="Experience editor sections">
        {(["content", "relations", "publication"] as const).map((name) => (
          <Button
            aria-selected={tab === name}
            key={name}
            onClick={() => setTab(name)}
            role="tab"
            variant={tab === name ? "primary" : "secondary"}
          >
            {name[0]?.toUpperCase()}
            {name.slice(1)}
            {name === "content" && localErrors ? ` (${localErrors})` : ""}
          </Button>
        ))}
      </div>

      {tab === "content" ? (
        <section className={styles.editorSection} role="tabpanel">
          <h2>Role content</h2>
          <div className={styles.fields}>
            <label htmlFor="companyName">
              Company
              <input
                aria-describedby={errors.companyName ? "companyName-error" : undefined}
                id="companyName"
                maxLength={160}
                onBlur={() => setErrors(validate(input))}
                onChange={(event) => change({ companyName: event.target.value })}
                value={input.companyName}
              />
            </label>
            <FieldError error={errors.companyName} id="companyName-error" />
            <label>
              Company HTTPS URL
              <input
                inputMode="url"
                onChange={(event) => change({ companyUrl: event.target.value || null })}
                placeholder="https://example.com"
                value={input.companyUrl ?? ""}
              />
            </label>
            <label htmlFor="roleTitle">
              Role title
              <input
                aria-describedby={errors.roleTitle ? "roleTitle-error" : undefined}
                id="roleTitle"
                maxLength={160}
                onBlur={() => setErrors(validate(input))}
                onChange={(event) => change({ roleTitle: event.target.value })}
                value={input.roleTitle}
              />
            </label>
            <FieldError error={errors.roleTitle} id="roleTitle-error" />
            <label>
              Employment type
              <select
                onChange={(event) =>
                  change({ employmentType: event.target.value as EmploymentType })
                }
                value={input.employmentType}
              >
                {employmentOptions.map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Work style
              <select
                onChange={(event) => change({ remoteStatus: event.target.value as RemoteStatus })}
                value={input.remoteStatus}
              >
                {remoteOptions.map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Location
              <input
                maxLength={160}
                onChange={(event) => change({ location: event.target.value || null })}
                value={input.location ?? ""}
              />
            </label>
            <label htmlFor="startDate">
              Start date
              <input
                id="startDate"
                onChange={(event) => change({ startDate: calendarDate(event.target.value) })}
                type="date"
                value={calendarValue(input.startDate)}
              />
            </label>
            <label htmlFor="endDate">
              End date
              <input
                aria-describedby="endDate-help"
                disabled={input.currentPosition}
                id="endDate"
                onChange={(event) =>
                  change({ endDate: event.target.value ? calendarDate(event.target.value) : null })
                }
                type="date"
                value={calendarValue(input.endDate)}
              />
            </label>
            <p className={styles.notice} id="endDate-help">
              Current positions have no end date. Turn off “Current position” to add one.
            </p>
            <label className={styles.check}>
              <input
                checked={input.currentPosition}
                onChange={(event) =>
                  change({
                    currentPosition: event.target.checked,
                    ...(event.target.checked ? { endDate: null } : {}),
                  })
                }
                type="checkbox"
              />
              Current position
            </label>
            <label className={styles.spanAll} htmlFor="shortSummary">
              Short summary
              <textarea
                aria-describedby={errors.shortSummary ? "shortSummary-error" : undefined}
                id="shortSummary"
                maxLength={500}
                onBlur={() => setErrors(validate(input))}
                onChange={(event) => change({ shortSummary: event.target.value })}
                value={input.shortSummary}
              />
            </label>
            <FieldError error={errors.shortSummary} id="shortSummary-error" />
            <label className={styles.spanAll}>
              Detailed description
              <textarea
                maxLength={20000}
                onChange={(event) => change({ detailedDescription: event.target.value || null })}
                value={input.detailedDescription ?? ""}
              />
            </label>
          </div>
          <OrderedField
            label="Responsibilities"
            onChange={(responsibilities) => change({ responsibilities })}
            values={input.responsibilities ?? []}
          />
          <OrderedField
            label="Achievements"
            onChange={(achievements) => change({ achievements })}
            values={input.achievements ?? []}
          />
          <OrderedField
            label="Technologies"
            onChange={(technologies) => change({ technologies })}
            values={input.technologies ?? []}
          />
        </section>
      ) : null}

      {tab === "relations" ? (
        <section className={styles.editorSection} role="tabpanel">
          <h2>Skill evidence</h2>
          <p>
            Select skills supported by this role. Hidden skills stay attached for administrators but
            never appear publicly.
          </p>
          {hiddenSelections.length ? (
            <p className={styles.warning} role="status">
              {hiddenSelections.length} selected{" "}
              {hiddenSelections.length === 1 ? "skill is" : "skills are"} hidden and will be omitted
              from the public timeline.
            </p>
          ) : null}
          <ul className={styles.skillList}>
            {skills.map((skill) => (
              <li className={styles.skillItem} key={skill.id}>
                <label className={styles.check}>
                  <input
                    checked={input.skillIds?.includes(skill.id) ?? false}
                    onChange={(event) =>
                      change({
                        skillIds: event.target.checked
                          ? [...(input.skillIds ?? []), skill.id]
                          : (input.skillIds ?? []).filter((id) => id !== skill.id),
                      })
                    }
                    type="checkbox"
                  />
                  <span>
                    <strong>{skill.name}</strong>
                    <small>{skill.visible ? "Visible" : "Hidden — admin only"}</small>
                  </span>
                </label>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {tab === "publication" ? (
        <section className={styles.editorSection} role="tabpanel">
          <h2>Publication</h2>
          <div className={styles.publicationCard}>
            <p>
              <strong>Visibility:</strong>{" "}
              {item.visible ? "Visible when effective" : "Hidden even when published"}
            </p>
            <p>
              <strong>Revision:</strong> Draft {item.draft.revisionNumber}
              {item.published ? ` · Live ${item.published.revisionNumber}` : " · Not yet published"}
            </p>
            <label>
              Schedule in {timezone}
              <input
                onChange={(event) => setSchedule(event.target.value)}
                type="datetime-local"
                value={schedule}
              />
            </label>
            <p className={styles.notice}>
              Leave blank to publish now. Scheduled times are interpreted in {timezone}; ambiguous
              or nonexistent daylight-saving times are rejected.
            </p>
            {schedule ? (
              (() => {
                try {
                  const utc = zonedLocalToUtc(schedule, timezone);
                  return (
                    <p>
                      <strong>Review:</strong> {formatInTimezone(utc, timezone)} ·{" "}
                      <span>{utc.toISOString()} UTC</span>
                    </p>
                  );
                } catch (caught) {
                  return (
                    <p className={styles.warning} role="alert">
                      {caught instanceof Error ? caught.message : "Invalid schedule."}
                    </p>
                  );
                }
              })()
            ) : (
              <p>
                <strong>Review:</strong> Publish now using database time.
              </p>
            )}
            <div className={styles.editorActions}>
              <Button
                disabled={busy}
                onClick={() => {
                  let publishAt: Date | undefined;
                  try {
                    publishAt = schedule ? zonedLocalToUtc(schedule, timezone) : undefined;
                  } catch (caught) {
                    setApiError(
                      new ApiError({
                        code: "INVALID_SCHEDULE",
                        message: caught instanceof Error ? caught.message : "Invalid schedule.",
                        status: 422,
                      }),
                    );
                    return;
                  }
                  const timing = publishAt
                    ? ` at ${formatInTimezone(publishAt, timezone)}`
                    : " now";
                  if (
                    !window.confirm(
                      `Publish ${item.visible ? "visibly" : "while hidden"}${timing}?`,
                    )
                  )
                    return;
                  void run(
                    () => api.publish(item, publishAt),
                    schedule ? "Publication scheduled." : "Experience published.",
                  );
                }}
              >
                Publish {schedule ? "on schedule" : "now"}
              </Button>
              {item.published && schedule ? (
                <Button
                  disabled={busy}
                  onClick={() => {
                    try {
                      const publishAt = zonedLocalToUtc(schedule, timezone);
                      void run(() => api.reschedule(item, publishAt), "Publication rescheduled.");
                    } catch (caught) {
                      setApiError(
                        new ApiError({
                          code: "INVALID_SCHEDULE",
                          message: caught instanceof Error ? caught.message : "Invalid schedule.",
                          status: 422,
                        }),
                      );
                    }
                  }}
                  variant="secondary"
                >
                  Reschedule only
                </Button>
              ) : null}
              {item.published ? (
                <Button
                  disabled={busy}
                  onClick={() => {
                    if (
                      window.confirm(
                        "Unpublish now? The draft and revision history remain available.",
                      )
                    )
                      void run(() => api.unpublish(item), "Experience unpublished.");
                  }}
                  variant="danger"
                >
                  Unpublish
                </Button>
              ) : null}
            </div>
          </div>
        </section>
      ) : null}
    </div>
  );
}

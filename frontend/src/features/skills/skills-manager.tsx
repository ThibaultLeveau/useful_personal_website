"use client";

import { useCallback, useState } from "react";

import { Button } from "@/components/ui/button";
import { LoadingPanel } from "@/components/ui/loading-panel";
import type { AdminSkillsListRequest } from "@/generated/api/src/apis/SkillsApi";
import type {
  PaginationData,
  SkillCategoryData,
  SkillCategoryInput,
  SkillData,
  SkillInput,
} from "@/generated/api/src/models";
import { useAuth } from "@/features/auth/auth-context";
import {
  FormStatus,
  optional,
  toApiError,
  useDeferredInitialLoad,
} from "@/features/site-configuration/configuration-form";
import { ApiError } from "@/lib/api";

import { adminSkillsApi, type AdminSkillsApiBoundary } from "./admin-api";
import styles from "./skills-admin.module.css";

function value(form: FormData, name: string): string {
  return String(form.get(name) ?? "").trim();
}

export function slugify(valueToNormalize: string): string {
  return valueToNormalize
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/gu, "")
    .replace(/[^a-zA-Z0-9]+/gu, "-")
    .replace(/^-+|-+$/gu, "")
    .toLowerCase()
    .slice(0, 80);
}

function categoryInput(form: FormData): SkillCategoryInput {
  return {
    description: optional(value(form, "description")),
    name: value(form, "name"),
    slug: value(form, "slug"),
  };
}

function skillInput(form: FormData): SkillInput {
  const rawScore = value(form, "proficiencyScore");
  return {
    associatedExperienceIds: [],
    associatedProjectIds: [],
    categoryId: value(form, "categoryId"),
    description: optional(value(form, "description")),
    featured: form.get("featured") === "on",
    iconKey: optional(value(form, "iconKey")),
    name: value(form, "name"),
    proficiencyLabel: optional(value(form, "proficiencyLabel")),
    proficiencyScore: rawScore ? Number(rawScore) : null,
    slug: value(form, "slug"),
    visible: form.get("visible") === "on",
    yearsExperience: value(form, "yearsExperience"),
  };
}

function replace<Item>(items: Item[], index: number, next: Item): Item[] {
  return items.map((item, itemIndex) => (itemIndex === index ? next : item));
}

function move<Item>(items: Item[], index: number, direction: -1 | 1): Item[] {
  const target = index + direction;
  if (target < 0 || target >= items.length) return items;
  const next = [...items];
  [next[index], next[target]] = [next[target] as Item, next[index] as Item];
  return next;
}

export function SkillsManager({ api = adminSkillsApi }: { api?: AdminSkillsApiBoundary }) {
  const auth = useAuth();
  const [categories, setCategories] = useState<SkillCategoryData[]>([]);
  const [skills, setSkills] = useState<SkillData[]>([]);
  const [pagination, setPagination] = useState<PaginationData | null>(null);
  const [activeFilters, setActiveFilters] = useState<AdminSkillsListRequest>({});
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [saved, setSaved] = useState<string | null>(null);

  const load = useCallback(
    async (filters: AdminSkillsListRequest = {}) => {
      setLoading(true);
      setError(null);
      try {
        const snapshot = await api.load(filters);
        setCategories(snapshot.categories);
        setPagination(snapshot.pagination);
        setSkills(snapshot.skills);
        setActiveFilters(filters);
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

  const completePositionView =
    !activeFilters.categoryId &&
    activeFilters.visible === undefined &&
    activeFilters.featured === undefined &&
    !activeFilters.search &&
    (!activeFilters.sort || activeFilters.sort === "position") &&
    (activeFilters.page ?? 1) === 1 &&
    pagination?.totalItems === skills.length;

  async function mutate(action: () => Promise<void>, message: string): Promise<boolean> {
    setBusy(true);
    setError(null);
    setSaved(null);
    try {
      await action();
      setSaved(message);
      return true;
    } catch (caught) {
      const next = toApiError(caught);
      setError(next);
      if (next.status === 401) auth.expireSession();
      return false;
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <LoadingPanel label="Loading skills workspace" />;

  return (
    <>
      <header className={styles.pageHeader}>
        <div>
          <p className="eyebrow">Content / Skills</p>
          <h1>Capability catalog</h1>
          <p>Organize public skills without exposing drafts, internal IDs, or future relations.</p>
        </div>
        <Button onClick={() => void load()} variant="secondary">
          Refresh
        </Button>
      </header>
      <FormStatus error={error} saved={saved} />
      {error?.code === "RESOURCE_VERSION_CONFLICT" ? (
        <Button onClick={() => void load()} variant="secondary">
          Reload current versions
        </Button>
      ) : null}

      <section className={styles.panel} aria-labelledby="categories-title">
        <header className={styles.panelHeader}>
          <div>
            <p className="eyebrow">Structure</p>
            <h2 id="categories-title">Categories</h2>
          </div>
          <span>{categories.length} total</span>
        </header>
        <CategoryCreate
          disabled={busy}
          onCreate={(input) =>
            mutate(async () => {
              const created = await api.createCategory(input);
              setCategories((current) => [...current, created]);
            }, "Category created.")
          }
        />
        <ol className={styles.list}>
          {categories.map((category, index) => (
            <li key={category.id}>
              <CategoryEditor
                category={category}
                disabled={busy}
                first={index === 0}
                last={index === categories.length - 1}
                onDelete={() =>
                  mutate(async () => {
                    await api.deleteCategory(category);
                    setCategories((current) => current.filter((item) => item.id !== category.id));
                  }, "Category deleted.")
                }
                onMove={(direction) =>
                  mutate(async () => {
                    const ordered = move(categories, index, direction);
                    setCategories(await api.reorderCategories(ordered));
                  }, "Category order saved.")
                }
                onSave={(input) =>
                  mutate(async () => {
                    const updated = await api.updateCategory(category, input);
                    setCategories((current) => replace(current, index, updated));
                  }, "Category saved.")
                }
              />
            </li>
          ))}
        </ol>
      </section>

      <section className={styles.panel} aria-labelledby="skills-title">
        <header className={styles.panelHeader}>
          <div>
            <p className="eyebrow">Entries</p>
            <h2 id="skills-title">Skills</h2>
          </div>
          <span>{skills.length} total</span>
        </header>
        <SkillFilters
          categories={categories}
          disabled={busy}
          filters={activeFilters}
          onApply={load}
        />
        {categories.length ? (
          <SkillCreate
            categories={categories}
            disabled={busy}
            onCreate={(input) =>
              mutate(async () => {
                await api.createSkill(input);
                await load(activeFilters);
              }, "Skill created. Its visibility setting controls public publication.")
            }
          />
        ) : (
          <p className={styles.notice}>Create a category before adding skills.</p>
        )}
        {categories.map((category) => {
          const categorySkills = skills
            .filter((skill) => skill.categoryId === category.id)
            .sort((left, right) => left.position - right.position);
          if (!categorySkills.length) return null;
          return (
            <section className={styles.skillGroup} key={category.id}>
              <h3>{category.name}</h3>
              <ol className={styles.list}>
                {categorySkills.map((skill, index) => (
                  <li key={skill.id}>
                    <SkillEditor
                      categories={categories}
                      disabled={busy}
                      first={index === 0}
                      last={index === categorySkills.length - 1}
                      onDelete={() =>
                        mutate(async () => {
                          await api.deleteSkill(skill);
                          await load(activeFilters);
                        }, "Skill deleted.")
                      }
                      onMove={(direction) =>
                        mutate(async () => {
                          const ordered = move(categorySkills, index, direction);
                          const updated = await api.reorderSkills(category.id, ordered);
                          setSkills((current) => [
                            ...current.filter((item) => item.categoryId !== category.id),
                            ...updated,
                          ]);
                        }, "Skill order saved.")
                      }
                      onSave={(input) =>
                        mutate(async () => {
                          await api.updateSkill(skill, input);
                          await load(activeFilters);
                        }, "Skill saved.")
                      }
                      reorderDisabled={!completePositionView}
                      skill={skill}
                    />
                  </li>
                ))}
              </ol>
            </section>
          );
        })}
        {pagination ? (
          <nav className={styles.pagination} aria-label="Skills pages">
            <Button
              disabled={busy || !pagination.hasPrevious}
              onClick={() =>
                void load({ ...activeFilters, page: Math.max(1, pagination.page - 1) })
              }
              variant="secondary"
            >
              Previous
            </Button>
            <span>
              Page {pagination.page} of {Math.max(1, pagination.totalPages)} ·{" "}
              {pagination.totalItems} skills
            </span>
            <Button
              disabled={busy || !pagination.hasNext}
              onClick={() => void load({ ...activeFilters, page: pagination.page + 1 })}
              variant="secondary"
            >
              Next
            </Button>
          </nav>
        ) : null}
      </section>
    </>
  );
}

function SkillFilters({
  categories,
  disabled,
  filters,
  onApply,
}: {
  categories: SkillCategoryData[];
  disabled: boolean;
  filters: AdminSkillsListRequest;
  onApply: (filters?: AdminSkillsListRequest) => Promise<void>;
}) {
  return (
    <form
      className={styles.filters}
      onSubmit={(event) => {
        event.preventDefault();
        const form = new FormData(event.currentTarget);
        const visible = value(form, "visible");
        const featured = value(form, "featured");
        const categoryId = value(form, "categoryId");
        const search = value(form, "search");
        const sort = value(form, "sort");
        void onApply({
          ...(categoryId ? { categoryId } : {}),
          ...(featured ? { featured: featured === "true" } : {}),
          page: 1,
          pageSize: 20,
          ...(search ? { search } : {}),
          ...(sort ? { sort } : {}),
          ...(visible ? { visible: visible === "true" } : {}),
        });
      }}
    >
      <h3>Filter catalog</h3>
      <label>
        Search
        <input defaultValue={filters.search ?? ""} maxLength={120} name="search" type="search" />
      </label>
      <label>
        Category
        <select defaultValue={filters.categoryId ?? ""} name="categoryId">
          <option value="">All</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        Visibility
        <select defaultValue={filters.visible?.toString() ?? ""} name="visible">
          <option value="">All</option>
          <option value="true">Published</option>
          <option value="false">Hidden</option>
        </select>
      </label>
      <label>
        Featured
        <select defaultValue={filters.featured?.toString() ?? ""} name="featured">
          <option value="">All</option>
          <option value="true">Featured</option>
          <option value="false">Standard</option>
        </select>
      </label>
      <label>
        Sort
        <select defaultValue={filters.sort ?? "position"} name="sort">
          <option value="position">Position</option>
          <option value="name">Name</option>
          <option value="-updated_at">Recently updated</option>
        </select>
      </label>
      <div className="button-row">
        <Button disabled={disabled} type="submit">
          Apply filters
        </Button>
        <Button disabled={disabled} onClick={() => void onApply({})} type="reset" variant="quiet">
          Clear
        </Button>
      </div>
    </form>
  );
}

function CategoryCreate({
  disabled,
  onCreate,
}: {
  disabled: boolean;
  onCreate: (input: SkillCategoryInput) => Promise<boolean>;
}) {
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  return (
    <form
      className={styles.createForm}
      onSubmit={(event) => {
        event.preventDefault();
        const form = event.currentTarget;
        void onCreate(categoryInput(new FormData(form))).then((saved) => {
          if (!saved) return;
          setName("");
          setSlug("");
          form.reset();
        });
      }}
    >
      <h3>New category</h3>
      <label>
        Name
        <input
          maxLength={120}
          name="name"
          onChange={(event) => {
            setName(event.target.value);
            setSlug(slugify(event.target.value));
          }}
          required
          value={name}
        />
      </label>
      <label>
        Slug
        <input
          maxLength={80}
          name="slug"
          onChange={(event) => setSlug(event.target.value)}
          pattern="[a-z0-9]+(-[a-z0-9]+)*"
          required
          value={slug}
        />
      </label>
      <label className={styles.wide}>
        Description
        <textarea maxLength={2000} name="description" />
      </label>
      <Button disabled={disabled} type="submit">
        Add category
      </Button>
    </form>
  );
}

function CategoryEditor({
  category,
  disabled,
  first,
  last,
  onDelete,
  onMove,
  onSave,
}: {
  category: SkillCategoryData;
  disabled: boolean;
  first: boolean;
  last: boolean;
  onDelete: () => Promise<boolean>;
  onMove: (direction: -1 | 1) => Promise<boolean>;
  onSave: (input: SkillCategoryInput) => Promise<boolean>;
}) {
  return (
    <form
      className={styles.item}
      onSubmit={(event) => {
        event.preventDefault();
        void onSave(categoryInput(new FormData(event.currentTarget)));
      }}
    >
      <div className={styles.itemTitle}>
        <strong>{category.name}</strong>
        <code>{category.slug}</code>
      </div>
      <div className={styles.fields}>
        <label>
          Name
          <input defaultValue={category.name} maxLength={120} name="name" required />
        </label>
        <label>
          Slug
          <input
            defaultValue={category.slug}
            maxLength={80}
            name="slug"
            pattern="[a-z0-9]+(-[a-z0-9]+)*"
            required
          />
        </label>
        <label className={styles.wide}>
          Description
          <textarea defaultValue={category.description ?? ""} maxLength={2000} name="description" />
        </label>
      </div>
      <div className="button-row">
        <Button disabled={disabled} type="submit">
          Save
        </Button>
        <Button
          aria-label={`Move ${category.name} up`}
          disabled={disabled || first}
          onClick={() => void onMove(-1)}
          type="button"
          variant="secondary"
        >
          Move up
        </Button>
        <Button
          aria-label={`Move ${category.name} down`}
          disabled={disabled || last}
          onClick={() => void onMove(1)}
          type="button"
          variant="secondary"
        >
          Move down
        </Button>
        <Button
          disabled={disabled}
          onClick={() => {
            if (window.confirm(`Delete empty category “${category.name}”?`)) void onDelete();
          }}
          type="button"
          variant="danger"
        >
          Delete
        </Button>
      </div>
    </form>
  );
}

function SkillCreate({
  categories,
  disabled,
  onCreate,
}: {
  categories: SkillCategoryData[];
  disabled: boolean;
  onCreate: (input: SkillInput) => Promise<boolean>;
}) {
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  return (
    <form
      className={styles.createForm}
      onSubmit={(event) => {
        event.preventDefault();
        void onCreate(skillInput(new FormData(event.currentTarget)));
      }}
    >
      <h3>New skill</h3>
      <label>
        Name
        <input
          maxLength={120}
          name="name"
          onChange={(event) => {
            setName(event.target.value);
            setSlug(slugify(event.target.value));
          }}
          required
          value={name}
        />
      </label>
      <label>
        Slug
        <input
          maxLength={80}
          name="slug"
          onChange={(event) => setSlug(event.target.value)}
          pattern="[a-z0-9]+(-[a-z0-9]+)*"
          required
          value={slug}
        />
      </label>
      <label>
        Category
        <select name="categoryId" required>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        Years experience
        <input
          inputMode="decimal"
          name="yearsExperience"
          pattern="(?:0|[1-9][0-9]{0,2})(?:\.[0-9]{1,2})?"
          placeholder="3.50"
          required
        />
      </label>
      <label className={styles.wide}>
        Description
        <textarea maxLength={2000} name="description" />
      </label>
      <SkillOptionalFields />
      <Button disabled={disabled} type="submit">
        Add skill
      </Button>
    </form>
  );
}

function SkillEditor({
  categories,
  disabled,
  first,
  last,
  onDelete,
  onMove,
  onSave,
  reorderDisabled,
  skill,
}: {
  categories: SkillCategoryData[];
  disabled: boolean;
  first: boolean;
  last: boolean;
  onDelete: () => Promise<boolean>;
  onMove: (direction: -1 | 1) => Promise<boolean>;
  onSave: (input: SkillInput) => Promise<boolean>;
  reorderDisabled: boolean;
  skill: SkillData;
}) {
  return (
    <form
      className={styles.item}
      onSubmit={(event) => {
        event.preventDefault();
        void onSave(skillInput(new FormData(event.currentTarget)));
      }}
    >
      <div className={styles.itemTitle}>
        <strong>{skill.name}</strong>
        <span className={skill.visible ? styles.live : styles.draft}>
          {skill.visible ? "Published" : "Hidden"}
        </span>
      </div>
      <div className={styles.fields}>
        <label>
          Name
          <input defaultValue={skill.name} maxLength={120} name="name" required />
        </label>
        <label>
          Slug
          <input
            defaultValue={skill.slug}
            maxLength={80}
            name="slug"
            pattern="[a-z0-9]+(-[a-z0-9]+)*"
            required
          />
        </label>
        <label>
          Category
          <select defaultValue={skill.categoryId} name="categoryId" required>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Years experience
          <input
            defaultValue={skill.yearsExperience}
            inputMode="decimal"
            name="yearsExperience"
            pattern="(?:0|[1-9][0-9]{0,2})(?:\.[0-9]{1,2})?"
            required
          />
        </label>
        <label className={styles.wide}>
          Description
          <textarea defaultValue={skill.description ?? ""} maxLength={2000} name="description" />
        </label>
        <SkillOptionalFields skill={skill} />
      </div>
      <fieldset className={styles.unavailable} disabled>
        <legend>Projects and experience relations</legend>
        <p>Unavailable until the Projects and Experience providers are delivered in M5 and M6.</p>
        <input aria-label="Associated projects" placeholder="No provider installed" />
      </fieldset>
      <div className="button-row">
        <Button disabled={disabled} type="submit">
          Save
        </Button>
        <Button
          aria-label={`Move ${skill.name} up`}
          disabled={disabled || reorderDisabled || first}
          onClick={() => void onMove(-1)}
          type="button"
          variant="secondary"
        >
          Move up
        </Button>
        <Button
          aria-label={`Move ${skill.name} down`}
          disabled={disabled || reorderDisabled || last}
          onClick={() => void onMove(1)}
          type="button"
          variant="secondary"
        >
          Move down
        </Button>
        <Button
          disabled={disabled}
          onClick={() => {
            if (window.confirm(`Delete skill “${skill.name}”?`)) void onDelete();
          }}
          type="button"
          variant="danger"
        >
          Delete
        </Button>
      </div>
    </form>
  );
}

function SkillOptionalFields({ skill }: { skill?: SkillData }) {
  return (
    <>
      <label>
        Proficiency label
        <input
          defaultValue={skill?.proficiencyLabel ?? ""}
          maxLength={80}
          name="proficiencyLabel"
        />
      </label>
      <label>
        Score (0–100)
        <input
          defaultValue={skill?.proficiencyScore ?? ""}
          max={100}
          min={0}
          name="proficiencyScore"
          type="number"
        />
      </label>
      <label>
        Icon key
        <input
          defaultValue={skill?.iconKey ?? ""}
          maxLength={64}
          name="iconKey"
          pattern="[a-z0-9]+(-[a-z0-9]+)*"
        />
      </label>
      <label className={styles.check}>
        <input defaultChecked={skill?.featured ?? false} name="featured" type="checkbox" /> Featured
      </label>
      <label className={styles.check}>
        <input defaultChecked={skill?.visible ?? true} name="visible" type="checkbox" /> Published
      </label>
    </>
  );
}

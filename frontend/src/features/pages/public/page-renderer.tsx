import Link from "next/link";
import type { Route } from "next";
import type { ReactNode } from "react";

import type {
  ActionConfig,
  Definition1,
  PublicPageBlockData,
  PublicPageData,
  ResolvedReferenceData,
} from "@/generated/api/src/models";

import { ResponsiveMediaImage } from "@/components/public/responsive-media-image";
import { SafeRenderedContent } from "@/features/blog/public/safe-rendered-content";
import styles from "./pages-public.module.css";

export const PAGE_BLOCK_TYPES = [
  "hero",
  "profile_summary",
  "call_to_action",
  "statistics",
  "skills_grid",
  "featured_skills",
  "experience_summary",
  "experience_list",
  "project_grid",
  "featured_projects",
  "latest_posts",
  "rich_text",
  "image",
  "image_with_text",
  "links_collection",
  "contact_callout",
  "testimonial",
  "divider",
  "spacer",
] as const;

type BlockType = (typeof PAGE_BLOCK_TYPES)[number];
type Renderer = (block: PublicPageBlockData) => ReactNode;

function href(action: ActionConfig, references: ResolvedReferenceData[]): string | null {
  return (
    action.destination ??
    references.find((reference) => reference.targetId === action.pageId)?.href ??
    null
  );
}

function Actions({
  actions,
  references,
}: {
  actions: ActionConfig[];
  references: ResolvedReferenceData[];
}) {
  return actions.length ? (
    <div className={styles.actions}>
      {actions.map((action) => {
        const destination = href(action, references);
        return destination ? (
          <Link
            className="button button--primary"
            href={destination as Route}
            key={`${action.label}-${destination}`}
            {...(action.newWindow ? { target: "_blank", rel: "noreferrer" } : {})}
          >
            {action.label}
          </Link>
        ) : null;
      })}
    </div>
  ) : null;
}

function References({ items }: { items: ResolvedReferenceData[] }) {
  return (
    <ul className={styles.referenceGrid}>
      {items.map((item) => (
        <li key={`${item.kind}-${item.targetId}`}>
          {item.href ? (
            <Link href={item.href as Route}>{item.label}</Link>
          ) : (
            <strong>{item.label}</strong>
          )}
          {item.description ? <p>{item.description}</p> : null}
        </li>
      ))}
    </ul>
  );
}

function Heading({ definition }: { definition: Definition1 }) {
  return definition.title || definition.subtitle || definition.description ? (
    <header className={styles.blockHeader}>
      {definition.title ? <h2>{definition.title}</h2> : null}
      {definition.subtitle ? <p className={styles.subtitle}>{definition.subtitle}</p> : null}
      {definition.description ? <p>{definition.description}</p> : null}
    </header>
  ) : null;
}

const collection: Renderer = (block) => (
  <>
    <Heading definition={block.definition} />
    <References items={block.references} />
  </>
);

const renderers: Record<BlockType, Renderer> = {
  hero: (block) => {
    if (block.definition.blockType !== "hero") return null;
    const { config } = block.definition;
    return (
      <div className={styles.hero}>
        <p className="eyebrow">{config.eyebrow ?? "Welcome"}</p>
        <h1>{config.heading}</h1>
        <p>{config.body}</p>
        <Actions actions={config.actions ?? []} references={block.references} />
      </div>
    );
  },
  profile_summary: (block) => {
    if (block.definition.blockType !== "profile_summary" || !block.profile) return null;
    const profile = block.profile;
    return (
      <>
        <Heading definition={block.definition} />
        <div className={styles.profile}>
          <div>
            <p className="eyebrow">Profile</p>
            <h2>{profile.fullName ?? "About"}</h2>
            <p>{profile.professionalTitle}</p>
          </div>
          <div>
            {block.definition.config.showBiography !== false ? (
              <p>{profile.shortBiography ?? profile.fullBiography}</p>
            ) : null}
            {block.definition.config.showLocation !== false && profile.location ? (
              <p>{profile.location}</p>
            ) : null}
          </div>
        </div>
      </>
    );
  },
  call_to_action: (block) =>
    block.definition.blockType === "call_to_action" ? (
      <div className={styles.callout}>
        <h2>{block.definition.config.heading}</h2>
        <p>{block.definition.config.body}</p>
        <Actions actions={block.definition.config.actions} references={block.references} />
      </div>
    ) : null,
  statistics: (block) =>
    block.definition.blockType === "statistics" ? (
      <>
        <Heading definition={block.definition} />
        <dl className={styles.statistics}>
          {block.definition.config.items.map((item) => (
            <div key={item.label}>
              <dt>{item.label}</dt>
              <dd>
                <strong>{item.value}</strong>
                {item.context ? <span>{item.context}</span> : null}
              </dd>
            </div>
          ))}
        </dl>
      </>
    ) : null,
  skills_grid: collection,
  featured_skills: collection,
  experience_summary: collection,
  experience_list: collection,
  project_grid: collection,
  featured_projects: collection,
  latest_posts: collection,
  rich_text: (block) =>
    block.definition.blockType === "rich_text" ? (
      <>
        <Heading definition={block.definition} />
        <SafeRenderedContent content={block.definition.config.content} headingFloor={2} />
      </>
    ) : null,
  image: (block) =>
    block.definition.blockType === "image" ? (
      <figure
        className={styles.mediaFigure}
        data-focal-point={block.definition.config.focalPoint ?? "center"}
      >
        <ResponsiveMediaImage
          alt={block.definition.config.alt}
          assetId={block.definition.config.mediaId}
          className={styles.mediaPicture ?? ""}
          sizes="(max-width: 767px) 100vw, 76rem"
        />
        {block.definition.config.caption ? (
          <figcaption>{block.definition.config.caption}</figcaption>
        ) : null}
      </figure>
    ) : null,
  image_with_text: (block) =>
    block.definition.blockType === "image_with_text" ? (
      <div
        className={styles.split}
        data-image-position={block.definition.config.imagePosition ?? "start"}
      >
        <figure
          className={styles.mediaFigure}
          data-focal-point={block.definition.config.focalPoint ?? "center"}
        >
          <ResponsiveMediaImage
            alt={block.definition.config.alt}
            assetId={block.definition.config.mediaId}
            className={styles.mediaPicture ?? ""}
            sizes="(max-width: 767px) 100vw, 38rem"
          />
          {block.definition.config.caption ? (
            <figcaption>{block.definition.config.caption}</figcaption>
          ) : null}
        </figure>
        <div>
          <h2>{block.definition.config.heading}</h2>
          <p>{block.definition.config.body}</p>
          {block.definition.config.action ? (
            <Actions actions={[block.definition.config.action]} references={block.references} />
          ) : null}
        </div>
      </div>
    ) : null,
  links_collection: (block) =>
    block.definition.blockType === "links_collection" ? (
      <>
        <Heading definition={block.definition} />
        <ul className={styles.links}>
          {block.definition.config.links.map((item) => (
            <li key={`${item.label}-${item.destination ?? item.pageId}`}>
              <strong>
                {(item.destination ??
                block.references.find((reference) => reference.targetId === item.pageId)?.href) ? (
                  <Link
                    href={
                      (item.destination ??
                        block.references.find((reference) => reference.targetId === item.pageId)
                          ?.href) as Route
                    }
                  >
                    {item.label}
                  </Link>
                ) : (
                  item.label
                )}
              </strong>
              {item.description ? <p>{item.description}</p> : null}
            </li>
          ))}
        </ul>
      </>
    ) : null,
  contact_callout: (block) =>
    block.definition.blockType === "contact_callout" ? (
      <div className={styles.callout}>
        <p className="eyebrow">Contact</p>
        <h2>{block.definition.config.heading}</h2>
        <p>{block.definition.config.body}</p>
        <Actions actions={block.definition.config.actions} references={block.references} />
      </div>
    ) : null,
  testimonial: (block) =>
    block.definition.blockType === "testimonial" ? (
      <figure className={styles.quote}>
        <blockquote>{block.definition.config.quote}</blockquote>
        <figcaption>
          {block.definition.config.attribution}
          {block.definition.config.context ? ` — ${block.definition.config.context}` : ""}
        </figcaption>
      </figure>
    ) : null,
  divider: (block) =>
    block.definition.blockType === "divider" ? (
      <hr className={styles[block.definition.config.style ?? "solid"]} />
    ) : null,
  spacer: (block) =>
    block.definition.blockType === "spacer" ? (
      <div
        aria-hidden="true"
        className={styles.spacer}
        data-size={block.definition.config.size ?? "medium"}
      />
    ) : null,
};

export function PageRenderer({ page }: { page: PublicPageData }) {
  return (
    <article className={styles.page} data-page-kind={page.routeKind}>
      {page.blocks.map((block) => {
        const type = block.definition.blockType as BlockType;
        const render = renderers[type];
        return render ? (
          <section
            className={styles.block}
            data-layout={block.definition.layout ?? "full"}
            data-theme={block.definition.theme ?? "default"}
            id={`block-${block.id}`}
            key={block.id}
          >
            {render(block)}
          </section>
        ) : null;
      })}
    </article>
  );
}

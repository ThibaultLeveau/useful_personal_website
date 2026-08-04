import type { Block, BlockType } from "@/generated/api/src/models";

export const BLOCK_TYPES: BlockType[] = [
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
];

const configs: Record<BlockType, object> = {
  hero: {
    heading: "A clear point of view",
    body: "Introduce the work and the value it creates.",
    eyebrow: "Portfolio",
    actions: [],
  },
  profile_summary: { showBiography: true, showLocation: true, aboutDestination: "/about" },
  call_to_action: {
    heading: "Start a conversation",
    body: "Describe the next useful step.",
    actions: [{ label: "Learn more", destination: "/about" }],
  },
  statistics: { items: [{ label: "Projects", value: "12", context: "Shipped outcomes" }] },
  skills_grid: { skillIds: [], maximumItems: 12 },
  featured_skills: { skillIds: [], maximumItems: 6 },
  experience_summary: { experienceIds: [], maximumItems: 3 },
  experience_list: { experienceIds: [], maximumItems: 12 },
  project_grid: { projectIds: [], maximumItems: 12 },
  featured_projects: { projectIds: [], maximumItems: 6 },
  latest_posts: { postIds: [], maximumItems: 6 },
  rich_text: { source: "## A section\n\nWrite controlled CommonMark here." },
  image: {
    alt: "Describe the image",
    purpose: "content",
    focalPoint: "center",
  },
  image_with_text: {
    alt: "Describe the image",
    heading: "A visual story",
    body: "Add context for this media.",
    imagePosition: "start",
    purpose: "content",
    focalPoint: "center",
  },
  links_collection: { links: [{ label: "Useful link", destination: "/" }] },
  contact_callout: {
    heading: "Get in touch",
    body: "Choose a safe contact route.",
    actions: [{ label: "About this work", destination: "/about" }],
  },
  testimonial: {
    quote: "Add a concise, attributable statement.",
    attribution: "Name",
    context: "Role",
  },
  divider: { style: "line" },
  spacer: { size: "medium", narrowSize: "small" },
};

export function newBlock(blockType: BlockType, mediaId?: string): Block {
  const requiresMedia = blockType === "image" || blockType === "image_with_text";
  if (requiresMedia && !mediaId) throw new Error("A ready media asset is required.");
  return {
    blockType,
    schemaVersion: 1,
    visible: true,
    layout: "full",
    theme: "default",
    config: requiresMedia ? { ...configs[blockType], mediaId } : configs[blockType],
  } as Block;
}

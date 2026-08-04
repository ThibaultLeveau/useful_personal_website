import Link from "next/link";

const sections = [
  {
    href: "/admin/profile",
    label: "Profile and privacy",
    description: "Edit biography, contact values, links, and explicit public-field approvals.",
  },
  {
    href: "/admin/settings",
    label: "Website settings",
    description: "Manage site identity, locale, theme policy, SEO, and public identifiers.",
  },
  {
    href: "/admin/navigation",
    label: "Navigation",
    description: "Order visible internal and HTTPS destinations in a two-level menu.",
  },
  {
    href: "/admin/footer",
    label: "Footer",
    description: "Configure ordered public columns, legal or social links, and footer text.",
  },
  {
    href: "/admin/media",
    label: "Media library",
    description: "Upload verified images, inspect usage, and manage safe previews.",
  },
  {
    href: "/admin/skills",
    label: "Skills",
    description: "Organize public capabilities into ordered categories and featured entries.",
  },
  {
    href: "/admin/experiences",
    label: "Experience",
    description: "Draft, preview, publish, schedule, and relate professional experience.",
  },
  {
    href: "/admin/projects",
    label: "Projects",
    description:
      "Build case studies with safe Markdown, evidence, media, and publication controls.",
  },
  {
    href: "/admin/blog",
    label: "Blog",
    description: "Manage articles, taxonomy, preview, scheduling, and related writing.",
  },
  {
    href: "/admin/pages",
    label: "Pages",
    description: "Compose the home page and custom routes from controlled content blocks.",
  },
  {
    href: "/admin/contacts",
    label: "Contacts",
    description: "Review private enquiries and apply explicit read, archive, or delete actions.",
  },
  {
    href: "/admin/api-tokens",
    label: "API tokens",
    description: "Issue, rotate, and revoke scoped integration credentials.",
  },
  {
    href: "/admin/audit",
    label: "Audit trail",
    description: "Inspect the immutable administrative event record and its safe metadata.",
  },
  {
    href: "/admin/health",
    label: "System health",
    description: "Check readiness categories without exposing infrastructure or secrets.",
  },
] as const;

export default function AdminPage() {
  return (
    <main className="admin-main" id="admin-main" tabIndex={-1}>
      <header className="admin-page-header">
        <div>
          <p className="eyebrow">Workspace / Overview</p>
          <h1>Site configuration</h1>
          <p>Choose a section. Every save is version-checked and audited.</p>
        </div>
      </header>
      <section className="admin-onboarding" aria-labelledby="onboarding-heading">
        <div>
          <p className="eyebrow">Recommended setup order</p>
          <h2 id="onboarding-heading">Publish deliberately.</h2>
        </div>
        <ol>
          <li>Set site identity, locale, and privacy-safe profile fields.</li>
          <li>Build navigation, footer, pages, and reusable media.</li>
          <li>Preview content before publishing or scheduling it.</li>
          <li>Verify contact policy, integrations, health, and audit history.</li>
        </ol>
        <Link className="button button--secondary" href="/" target="_blank">
          View public site
        </Link>
      </section>
      <div className="admin-dashboard">
        {sections.map((section, index) => (
          <Link href={{ pathname: section.href }} key={section.href}>
            <span aria-hidden="true">0{index + 1}</span>
            <strong>{section.label}</strong>
            <p>{section.description}</p>
          </Link>
        ))}
      </div>
    </main>
  );
}

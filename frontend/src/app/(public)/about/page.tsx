import type { Metadata } from "next";

import { EmptyState } from "@/components/ui/empty-state";
import { ResponsiveMediaImage } from "@/components/public/responsive-media-image";
import { getPublicProfile, getPublicSite } from "@/features/site-configuration/public-api";
import { publicMetadata } from "@/lib/discovery";

export const dynamic = "force-dynamic";

export async function generateMetadata(): Promise<Metadata> {
  try {
    const [profile, site] = await Promise.all([getPublicProfile(), getPublicSite()]);
    const title = profile.fullName ? `About ${profile.fullName}` : "About";
    return publicMetadata({
      canonicalPath: "/about",
      title: site.seoTitleSuffix ? `${title} | ${site.seoTitleSuffix}` : title,
      description:
        profile.shortBiography ??
        site.seoDescription ??
        site.defaultDescription ??
        "Published biography, work preferences, and contact links.",
    });
  } catch {
    return { title: "About" };
  }
}

async function loadPublicProfile() {
  try {
    return await getPublicProfile();
  } catch {
    return null;
  }
}

export default async function AboutPage() {
  const profile = await loadPublicProfile();
  if (!profile) {
    return (
      <EmptyState
        description="The published profile could not be loaded. Try again shortly."
        eyebrow="About"
        title="The profile is temporarily unavailable."
      />
    );
  }
  if (!profile.configured) {
    return (
      <EmptyState
        description="The site owner has not approved any profile fields for publication."
        eyebrow="About"
        title="No public profile is available."
      />
    );
  }
  return (
    <article className="about-profile">
      <header>
        <p className="eyebrow">About</p>
        {profile.fullName ? <h1>{profile.fullName}</h1> : null}
        {profile.professionalTitle ? <p>{profile.professionalTitle}</p> : null}
        {profile.availability ? (
          <p className="about-profile__availability">{profile.availability}</p>
        ) : null}
      </header>
      {profile.profileImageId ? (
        <ResponsiveMediaImage
          alt={profile.fullName ? `Portrait of ${profile.fullName}` : "Profile portrait"}
          assetId={profile.profileImageId}
          className="about-profile__media"
          eager
          sizes="(min-width: 64rem) 28rem, 80vw"
        />
      ) : null}
      {profile.shortBiography ? (
        <p className="about-profile__lead">{profile.shortBiography}</p>
      ) : null}
      {profile.fullBiography ? (
        <div className="about-profile__body">{profile.fullBiography}</div>
      ) : null}
      {profile.location ? (
        <section>
          <h2>Location</h2>
          <p>{profile.location}</p>
        </section>
      ) : null}
      {profile.personalValues?.length ? (
        <section>
          <h2>Values</h2>
          <ul className="tag-list">
            {profile.personalValues.map((value) => (
              <li key={value}>{value}</li>
            ))}
          </ul>
        </section>
      ) : null}
      {profile.workPreferences?.length ? (
        <section>
          <h2>Ways of working</h2>
          <ul>
            {profile.workPreferences.map((preference) => (
              <li key={preference}>{preference}</li>
            ))}
          </ul>
        </section>
      ) : null}
      {profile.email || profile.githubUrl || profile.linkedinUrl || profile.resumeUrl ? (
        <section>
          <h2>Links and contact</h2>
          <ul>
            {profile.email ? (
              <li>
                <a href={`mailto:${profile.email}`}>Email</a>
              </li>
            ) : null}
            {[
              ["GitHub", profile.githubUrl],
              ["LinkedIn", profile.linkedinUrl],
              ["Résumé", profile.resumeUrl],
            ].map(([label, href]) =>
              href ? (
                <li key={label}>
                  <a href={href} rel="noopener noreferrer" target="_blank">
                    {label}
                  </a>
                </li>
              ) : null,
            )}
          </ul>
        </section>
      ) : null}
    </article>
  );
}

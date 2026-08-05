import type { Metadata } from "next";

import { getPublicSite } from "@/features/site-configuration/public-api";
import { publicMetadata } from "@/lib/discovery";

export const metadata: Metadata = publicMetadata({
  canonicalPath: "/privacy",
  title: "Privacy notice",
  description: "How private contact enquiries are processed and retained.",
});

async function publicIdentity(): Promise<{ email?: string; name?: string }> {
  try {
    const site = await getPublicSite();
    return {
      ...(site.contactEmail ? { email: site.contactEmail } : {}),
      ...(site.websiteName ? { name: site.websiteName } : {}),
    };
  } catch {
    return {};
  }
}

export default async function PrivacyPage() {
  const identity = await publicIdentity();
  return (
    <article className="page-shell prose-page">
      <p className="eyebrow">Privacy</p>
      <h1>Contact form privacy notice</h1>
      {identity.name && identity.email ? (
        <p>
          The data controller is {identity.name}. Privacy requests can be sent to{" "}
          <a href={`mailto:${identity.email}`}>{identity.email}</a>.
        </p>
      ) : (
        <p>
          This deployment is not ready for public contact collection until the administrator
          configures the controller name and public contact email.
        </p>
      )}
      <p>
        When you use the contact form, this site stores the name, email address, subject, message,
        consent time, policy version, and form source that you submit. These details are used only
        to review and respond to your enquiry. Processing is based on the consent requested beside
        the form; you may withdraw it by contacting the controller.
      </p>
      <p>
        Messages are private to the authenticated administrator. They are retained for no more than
        365 days, then removed by an operator-controlled retention process. Security controls use a
        rotating one-way network pseudonym; the raw network address is not stored with the
        submission. Data is hosted on the controller&apos;s VPS and is not sold or used for
        advertising.
      </p>
      <p>
        You may request access, correction, deletion, restriction, or a copy of your submitted data,
        and may withdraw consent. You may also complain to the{" "}
        <a href="https://www.cnil.fr/fr/plaintes" rel="noreferrer">
          French data-protection authority (CNIL)
        </a>
        . No automated decision-making is performed. Policy version:{" "}
        <strong>privacy-2026-08</strong>.
      </p>
    </article>
  );
}

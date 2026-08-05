import type { Metadata } from "next";

import { getPublicSite } from "@/features/site-configuration/public-api";
import { publicMetadata } from "@/lib/discovery";

export const metadata: Metadata = publicMetadata({
  canonicalPath: "/legal",
  title: "Legal notice",
  description: "Publisher and hosting information for this personal website.",
});

export default async function LegalPage() {
  let name: string | undefined;
  let email: string | undefined;
  try {
    const site = await getPublicSite();
    name = site.websiteName ?? undefined;
    email = site.contactEmail ?? undefined;
  } catch {
    // The explicit incomplete state remains visible when configuration is unavailable.
  }

  return (
    <article className="page-shell prose-page">
      <p className="eyebrow">Legal</p>
      <h1>Legal notice</h1>
      {name && email ? (
        <>
          <p>
            This personal website is published by {name}. Contact:{" "}
            <a href={`mailto:${email}`}>{email}</a>.
          </p>
          <p>The publication director and data controller is {name}.</p>
        </>
      ) : (
        <p>
          Publisher identity is incomplete. Configure the website name and public contact email
          before production release.
        </p>
      )}
      <p>
        Hosting infrastructure: Hostinger International Ltd., 61 Lordou Vironos Street, 6023
        Larnaca, Cyprus. The application and its private media are operated on the publisher&apos;s
        VPS.
      </p>
      <p>
        Unless otherwise indicated, the website&apos;s original text and visual content belongs to
        its publisher. The application source code is available under the MIT License.
      </p>
    </article>
  );
}

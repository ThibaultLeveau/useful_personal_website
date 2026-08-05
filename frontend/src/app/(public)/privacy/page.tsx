import type { Metadata } from "next";
import { publicMetadata } from "@/lib/discovery";
export const metadata: Metadata = publicMetadata({
  canonicalPath: "/privacy",
  title: "Privacy notice",
  description: "How private contact enquiries are processed and retained.",
});
export default function PrivacyPage() {
  return (
    <main className="page-shell prose-page">
      <p className="eyebrow">Privacy</p>
      <h1>Contact form privacy notice</h1>
      <p>
        When you use the contact form, this site stores the name, email address, subject, message,
        consent time, policy version, and form source that you submit. These details are used only
        to review and respond to your enquiry.
      </p>
      <p>
        Messages are private to authenticated site administrators. They are retained for up to 365
        days by default, then removed by an operator-controlled retention process. Security controls
        use a rotating one-way network pseudonym; the raw network address is not stored with the
        submission.
      </p>
      <p>
        This deployment must publish the operator’s identity, lawful basis, jurisdiction-specific
        rights, and contact details before production release. Policy version:{" "}
        <strong>deployment configured</strong>.
      </p>
    </main>
  );
}

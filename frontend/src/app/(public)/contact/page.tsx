import type { Metadata } from "next";
import { ContactForm } from "@/features/contacts/contact-form";
import { publicMetadata } from "@/lib/discovery";
export const metadata: Metadata = publicMetadata({
  canonicalPath: "/contact",
  title: "Contact",
  description: "Send a private message.",
});
export default function ContactPage() {
  return (
    <div className="page-shell contact-page">
      <header>
        <p className="eyebrow">Contact</p>
        <h1>Let’s start a conversation.</h1>
        <p>Use this form for project enquiries and thoughtful notes.</p>
      </header>
      <ContactForm />
    </div>
  );
}

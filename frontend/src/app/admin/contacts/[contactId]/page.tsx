import { ContactDetail } from "@/features/contacts/contact-detail";
export default async function ContactPage({ params }: { params: Promise<{ contactId: string }> }) {
  const { contactId } = await params;
  return <ContactDetail id={contactId} />;
}

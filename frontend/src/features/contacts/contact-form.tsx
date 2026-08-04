"use client";
import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";
import type { ContactFormContextData } from "@/generated/api/src/models";
import { contactApi } from "./api";

export function ContactForm() {
  const [context, setContext] = useState<ContactFormContextData | null>(null);
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  useEffect(() => {
    void contactApi
      .context()
      .then(setContext)
      .catch(() => setStatus("error"));
  }, []);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!context) return;
    setStatus("sending");
    const form = new FormData(event.currentTarget);
    const body = {
      name: String(form.get("name") ?? ""),
      email: String(form.get("email") ?? ""),
      subject: String(form.get("subject") ?? ""),
      message: String(form.get("message") ?? ""),
      consent: form.get("consent") === "on",
      website: String(form.get("website") ?? ""),
      policyVersion: context.policyVersion,
      source: context.source,
      issuedAt: context.issuedAt,
      proof: context.proof,
    };
    try {
      await contactApi.submit(body);
      setStatus("sent");
      event.currentTarget.reset();
    } catch {
      setStatus("error");
    }
  }
  if (status === "sent")
    return (
      <section className="contact-panel" role="status">
        <p className="eyebrow">Message received</p>
        <h1>Thank you.</h1>
        <p>
          Your message was accepted securely. I’ll respond using the email address you provided.
        </p>
      </section>
    );
  return (
    <form className="contact-form" onSubmit={submit} aria-busy={status === "sending"}>
      <div>
        <label htmlFor="contact-name">Name</label>
        <input id="contact-name" name="name" autoComplete="name" maxLength={120} required />
      </div>
      <div>
        <label htmlFor="contact-email">Email</label>
        <input
          id="contact-email"
          name="email"
          type="email"
          autoComplete="email"
          maxLength={254}
          required
        />
      </div>
      <div>
        <label htmlFor="contact-subject">Subject</label>
        <input id="contact-subject" name="subject" maxLength={180} required />
      </div>
      <div>
        <label htmlFor="contact-message">Message</label>
        <textarea id="contact-message" name="message" rows={8} maxLength={5000} required />
      </div>
      <div className="contact-honeypot" aria-hidden="true">
        <label htmlFor="website">Website</label>
        <input id="website" name="website" tabIndex={-1} autoComplete="off" />
      </div>
      <label className="contact-consent">
        <input type="checkbox" name="consent" required /> I consent to this message being stored and
        processed as described in the <Link href="/privacy">privacy notice</Link>.
      </label>
      {status === "error" ? (
        <p role="alert">
          Your message could not be accepted. Check the fields and try again later.
        </p>
      ) : null}
      <button className="button" disabled={!context || status === "sending"} type="submit">
        {status === "sending" ? "Sending…" : "Send message"}
      </button>
    </form>
  );
}

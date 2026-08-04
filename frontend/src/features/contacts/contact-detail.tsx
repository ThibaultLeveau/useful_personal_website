"use client";
import { useEffect, useState } from "react";
import type { Route } from "next";
import { useRouter } from "next/navigation";
import type { ContactDetailData } from "@/generated/api/src/models";
import { contactApi } from "./api";
export function ContactDetail({ id }: { id: string }) {
  const [item, setItem] = useState<ContactDetailData | null>(null);
  const [error, setError] = useState(false);
  const router = useRouter();
  useEffect(() => {
    void contactApi
      .get(id)
      .then(setItem)
      .catch(() => setError(true));
  }, [id]);
  async function transition(state: "read" | "archived") {
    if (!item) return;
    try {
      setItem(await contactApi.transition(item, state));
    } catch {
      setError(true);
    }
  }
  async function remove() {
    if (!item || !confirm("Permanently delete this private message? This cannot be undone."))
      return;
    try {
      await contactApi.delete(item);
      router.push("/admin/contacts" as Route);
    } catch {
      setError(true);
    }
  }
  if (error)
    return (
      <main className="admin-page">
        <p role="alert">The message could not be loaded or changed.</p>
      </main>
    );
  if (!item)
    return (
      <main className="admin-page">
        <p>Loading message…</p>
      </main>
    );
  return (
    <main className="admin-page contact-detail">
      <header>
        <p className="eyebrow">{item.state}</p>
        <h1>{item.subject}</h1>
        <p>
          {item.name} · <a href={`mailto:${item.email}`}>{item.email}</a>
        </p>
      </header>
      <article>
        <p className="contact-message">{item.message}</p>
      </article>
      <dl>
        <div>
          <dt>Received</dt>
          <dd>{item.createdAt.toLocaleString()}</dd>
        </div>
        <div>
          <dt>Consent recorded</dt>
          <dd>
            {item.consentedAt.toLocaleString()} · {item.policyVersion}
          </dd>
        </div>
      </dl>
      <div className="button-row">
        {item.state === "unread" ? (
          <button onClick={() => void transition("read")}>Mark read</button>
        ) : null}
        {item.state === "read" ? (
          <button onClick={() => void transition("archived")}>Archive</button>
        ) : null}
        {item.state === "archived" ? (
          <button onClick={() => void transition("read")}>Restore to read</button>
        ) : null}
        <button className="danger" onClick={() => void remove()}>
          Delete permanently
        </button>
      </div>
    </main>
  );
}

"use client";
import Link from "next/link";
import type { Route } from "next";
import { useEffect, useState } from "react";
import type { ContactState, ContactSummaryData } from "@/generated/api/src/models";
import { contactApi } from "./api";
export function ContactInbox() {
  const [items, setItems] = useState<ContactSummaryData[]>([]);
  const [state, setState] = useState<ContactState>("unread");
  const [error, setError] = useState(false);
  useEffect(() => {
    void contactApi
      .list(state)
      .then(setItems)
      .catch(() => setError(true));
  }, [state]);
  return (
    <main className="admin-page">
      <header className="admin-page__header">
        <div>
          <p className="eyebrow">Private inbox</p>
          <h1>Contacts</h1>
        </div>
        <label>
          State{" "}
          <select
            value={state}
            onChange={(event) => {
              setError(false);
              setState(event.target.value as ContactState);
            }}
          >
            <option value="unread">Unread</option>
            <option value="read">Read</option>
            <option value="archived">Archived</option>
          </select>
        </label>
      </header>
      {error ? (
        <p role="alert">The inbox could not be loaded.</p>
      ) : items.length === 0 ? (
        <p className="empty-state">No messages in this view.</p>
      ) : (
        <ul className="contact-list">
          {items.map((item) => (
            <li key={item.id}>
              <Link href={`/admin/contacts/${item.id}` as Route}>
                <span>
                  <strong>{item.subject}</strong>
                  <small>
                    {item.name} · {item.email}
                  </small>
                </span>
                <time dateTime={item.createdAt.toISOString()}>
                  {item.createdAt.toLocaleString()}
                </time>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}

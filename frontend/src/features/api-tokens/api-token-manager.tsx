"use client";
import { useEffect, useState, type FormEvent } from "react";
import type { ApiTokenData, ApiTokenScope, ApiTokenSecretData } from "@/generated/api/src/models";
import { apiTokenApi } from "./api";
const labels: Record<string, string> = {
  "content:read": "Read content",
  "content:write": "Write content",
  "media:read": "Read media",
  "media:write": "Write media",
  "contacts:read": "Read contacts",
  "admin:read": "Read system information",
};
function defaultExpiry() {
  const date = new Date();
  date.setUTCDate(date.getUTCDate() + 90);
  return date.toISOString().slice(0, 10);
}
export function ApiTokenManager() {
  const [items, setItems] = useState<ApiTokenData[]>([]);
  const [scopes, setScopes] = useState<ApiTokenScope[]>([]);
  const [secret, setSecret] = useState<ApiTokenSecretData | null>(null);
  const [status, setStatus] = useState("Loading tokens…");
  const [busy, setBusy] = useState(false);
  async function load() {
    const [nextItems, nextScopes] = await Promise.all([apiTokenApi.list(), apiTokenApi.scopes()]);
    setItems(nextItems);
    setScopes(nextScopes);
    setStatus(nextItems.length ? "" : "No API tokens yet.");
  }
  useEffect(() => {
    void Promise.all([apiTokenApi.list(), apiTokenApi.scopes()])
      .then(([nextItems, nextScopes]) => {
        setItems(nextItems);
        setScopes(nextScopes);
        setStatus(nextItems.length ? "" : "No API tokens yet.");
      })
      .catch(() => setStatus("Tokens could not be loaded."));
  }, []);
  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    const form = event.currentTarget;
    const data = new FormData(form);
    const selected = new Set(data.getAll("scope").map(String) as ApiTokenScope[]);
    const noExpiry = data.get("no_expiry") === "on";
    const rawExpiry = String(data.get("expiry") ?? "");
    try {
      const created = await apiTokenApi.create({
        name: String(data.get("name") ?? ""),
        scopes: selected,
        expiresAt: noExpiry ? null : new Date(`${rawExpiry}T23:59:59Z`),
        confirmNoExpiry: noExpiry,
      });
      setSecret(created);
      await load();
      form.reset();
    } catch {
      setStatus("The token could not be created. Review the fields and try again.");
    } finally {
      setBusy(false);
    }
  }
  async function copy() {
    if (secret) {
      await navigator.clipboard.writeText(secret.plaintextToken);
      setStatus("Token copied. Store it securely; it will not be shown again.");
    }
  }
  function closeSecret() {
    setSecret(null);
    setStatus("Secret hidden permanently from this page.");
  }
  async function rotate(item: ApiTokenData) {
    if (!confirm(`Rotate ${item.name}? The current secret will stop working immediately.`)) return;
    setBusy(true);
    try {
      const rotated = await apiTokenApi.rotate(item, {
        expiresAt: new Date(`${defaultExpiry()}T23:59:59Z`),
        confirmNoExpiry: false,
      });
      setSecret(rotated);
      await load();
    } catch {
      setStatus("The token could not be rotated.");
    } finally {
      setBusy(false);
    }
  }
  async function revoke(item: ApiTokenData) {
    if (!confirm(`Revoke ${item.name}? Integrations using it will stop immediately.`)) return;
    setBusy(true);
    try {
      await apiTokenApi.revoke(item);
      await load();
      setStatus("Token revoked.");
    } catch {
      setStatus("The token could not be revoked.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="admin-page token-manager">
      <header>
        <p className="eyebrow">Security / API access</p>
        <h1>API tokens</h1>
        <p>Create least-privilege credentials for external integrations. Secrets appear once.</p>
      </header>
      {secret ? (
        <section className="token-secret" role="alert" aria-labelledby="token-secret-title">
          <h2 id="token-secret-title">Copy this token now</h2>
          <p>This is the only time the complete secret is available.</p>
          <code>{secret.plaintextToken}</code>
          <div className="button-row">
            <button onClick={() => void copy()}>Copy token</button>
            <button onClick={closeSecret}>I stored it securely</button>
          </div>
        </section>
      ) : null}
      <section className="token-create">
        <h2>Create token</h2>
        <form onSubmit={create}>
          <label>
            Name
            <input name="name" maxLength={80} required />
          </label>
          <fieldset>
            <legend>Scopes</legend>
            {scopes.map((scope) => (
              <label key={scope}>
                <input type="checkbox" name="scope" value={scope} />
                {labels[scope] ?? scope}
              </label>
            ))}
          </fieldset>
          <label>
            Expiry (90 days by default)
            <input type="date" name="expiry" defaultValue={defaultExpiry()} />
          </label>
          <label>
            <input type="checkbox" name="no_expiry" />
            No expiry — I understand this increases risk
          </label>
          <button disabled={busy} type="submit">
            Create token
          </button>
        </form>
      </section>
      <section>
        <h2>Token inventory</h2>
        <p role="status">{status}</p>
        {items.length ? (
          <div className="token-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Status</th>
                  <th>Scopes</th>
                  <th>Secret suffix</th>
                  <th>Last used</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    <th scope="row">{item.name}</th>
                    <td>{item.status}</td>
                    <td>{item.scopes.map((scope) => labels[scope] ?? scope).join(", ")}</td>
                    <td>
                      <code>…{item.displaySuffix}</code>
                    </td>
                    <td>{item.lastUsedAt?.toLocaleString() ?? "Never"}</td>
                    <td>
                      <div className="button-row">
                        {item.status === "active" ? (
                          <>
                            <button disabled={busy} onClick={() => void rotate(item)}>
                              Rotate
                            </button>
                            <button
                              disabled={busy}
                              className="danger"
                              onClick={() => void revoke(item)}
                            >
                              Revoke
                            </button>
                          </>
                        ) : (
                          "—"
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>
    </main>
  );
}

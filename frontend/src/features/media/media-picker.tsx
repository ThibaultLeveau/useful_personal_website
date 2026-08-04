"use client";

import type { Route } from "next";
import Link from "next/link";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import type { MediaAssetData } from "@/generated/api/src/models";
import { ApiError } from "@/lib/api";

import { adminMediaApi, type AdminMediaApiBoundary } from "./admin-api";
import styles from "./media-picker.module.css";

function preview(asset: MediaAssetData | undefined): string | undefined {
  if (!asset) return undefined;
  return (
    asset.variants
      .filter((variant) => variant.format === "webp")
      .sort((left, right) => Math.abs(left.width - 320) - Math.abs(right.width - 320))[0]
      ?.adminUrl ?? asset.variants[0]?.adminUrl
  );
}

export function MediaPicker({
  api = adminMediaApi,
  description,
  disabled = false,
  label,
  onChange,
  value,
}: {
  api?: AdminMediaApiBoundary;
  description: string;
  disabled?: boolean;
  label: string;
  onChange: (assetId: string | null) => void;
  value: string | null;
}) {
  const [items, setItems] = useState<MediaAssetData[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let current = true;
    const handle = window.setTimeout(
      () => {
        setLoading(true);
        setError("");
        void api
          .list({ page: 1, pageSize: 100, ...(search.trim() ? { search: search.trim() } : {}) })
          .then((snapshot) => {
            if (current) setItems(snapshot.items.filter((item) => item.status === "ready"));
          })
          .catch((caught: unknown) => {
            if (!current) return;
            setError(caught instanceof ApiError ? caught.message : "Media could not be loaded.");
          })
          .finally(() => {
            if (current) setLoading(false);
          });
      },
      search ? 250 : 0,
    );
    return () => {
      current = false;
      window.clearTimeout(handle);
    };
  }, [api, search]);

  const selected = items.find((item) => item.id === value);
  const url = preview(selected);
  return (
    <fieldset className={styles.picker} disabled={disabled}>
      <legend>{label}</legend>
      <p>{description}</p>
      <div className={styles.controls}>
        <label>
          <span>Search library</span>
          <input
            maxLength={120}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search display names"
            value={search}
          />
        </label>
        <label>
          <span>Selected image</span>
          <select
            aria-busy={loading}
            onChange={(event) => onChange(event.target.value || null)}
            value={value ?? ""}
          >
            <option value="">No image</option>
            {value && !selected ? <option value={value}>Current image</option> : null}
            {items.map((item) => (
              <option key={item.id} value={item.id}>
                {item.displayName} · {item.width ?? "?"} × {item.height ?? "?"}
              </option>
            ))}
          </select>
        </label>
      </div>
      {error ? (
        <p className={styles.error} role="alert">
          {error}
        </p>
      ) : null}
      {selected ? (
        <div className={styles.selection}>
          {url ? (
            // Private authenticated previews cannot use the server-side Next optimizer.
            // eslint-disable-next-line @next/next/no-img-element
            <img alt="" height={selected.height ?? 160} src={url} width={selected.width ?? 240} />
          ) : null}
          <div>
            <strong>{selected.displayName}</strong>
            <span>
              {selected.detectedFormat?.toUpperCase()} · {selected.width} × {selected.height}
            </span>
            <Button onClick={() => onChange(null)} variant="quiet">
              Clear image
            </Button>
          </div>
        </div>
      ) : null}
      <Link href={"/admin/media" as Route}>Open the full media library</Link>
    </fieldset>
  );
}

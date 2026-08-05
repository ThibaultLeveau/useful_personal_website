import Link from "next/link";

import { Surface } from "@/components/ui/surface";

export default function NotFound() {
  return (
    <main className="system-page" id="main-content">
      <Surface className="empty-state">
        <p className="eyebrow">404 / Not found</p>
        <h1 className="empty-state__title">This page is unavailable.</h1>
        <p className="empty-state__description">
          The address may be unknown, unpublished, hidden, or no longer available.
        </p>
        <Link className="button button--primary" href="/">
          Return home
        </Link>
      </Surface>
    </main>
  );
}

"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Surface } from "@/components/ui/surface";

export default function ErrorPage({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="system-page" id="main-content">
      <Surface className="empty-state" role="alert">
        <p className="eyebrow">Unable to render this page</p>
        <h1 className="empty-state__title">A safe recovery is available.</h1>
        <p className="empty-state__description">
          The page could not be loaded. No internal error details are displayed.
        </p>
        <div className="button-row">
          <Button onClick={reset}>Try again</Button>
          <Link className="button button--secondary" href="/">
            Return home
          </Link>
        </div>
      </Surface>
    </main>
  );
}

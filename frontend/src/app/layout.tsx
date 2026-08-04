import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import { ThemeInitializer } from "@/components/ui/theme-initializer";
import { publicOrigin } from "@/lib/discovery";

import "./globals.css";

export const metadata: Metadata = {
  metadataBase: publicOrigin(),
  title: {
    default: "Personal website",
    template: "%s",
  },
  description: "A configurable personal website.",
  applicationName: "Personal website",
  referrer: "strict-origin-when-cross-origin",
  openGraph: {
    type: "website",
    siteName: "Personal website",
    locale: "en_US",
  },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  colorScheme: "light dark",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <ThemeInitializer />
      </head>
      <body className="min-h-screen bg-[var(--canvas)] text-[var(--text)] antialiased">
        {children}
      </body>
    </html>
  );
}

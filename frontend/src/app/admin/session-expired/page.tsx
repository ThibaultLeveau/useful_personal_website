import type { Metadata } from "next";

import { SessionExpiredScreen } from "@/features/auth";

export const metadata: Metadata = {
  title: "Session expired | Administration",
  robots: { index: false, follow: false },
};

export default function SessionExpiredPage() {
  return <SessionExpiredScreen />;
}

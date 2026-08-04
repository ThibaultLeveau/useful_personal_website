import type { Metadata } from "next";

import { AccountScreen } from "@/features/auth";

export const metadata: Metadata = {
  title: "Account security | Administration",
  robots: { index: false, follow: false },
};

export default function AccountPage() {
  return <AccountScreen />;
}

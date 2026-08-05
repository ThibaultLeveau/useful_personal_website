import type { Metadata } from "next";

import { ChangePasswordScreen } from "@/features/auth";

export const metadata: Metadata = {
  title: "Change password | Administration",
  robots: { index: false, follow: false },
};

export default function ChangePasswordPage() {
  return <ChangePasswordScreen />;
}

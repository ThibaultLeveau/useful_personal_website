import type { Metadata } from "next";

import { LoginScreen } from "@/features/auth";

export const metadata: Metadata = {
  title: "Sign in | Administration",
  robots: { index: false, follow: false },
};

export default function LoginPage() {
  return <LoginScreen />;
}

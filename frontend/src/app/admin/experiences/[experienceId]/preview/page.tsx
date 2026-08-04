import type { Metadata } from "next";

import { ExperiencePreview } from "@/features/experiences/admin/experience-preview";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Draft experience preview",
  robots: { follow: false, index: false },
};

type Params = Promise<{ experienceId: string }>;

export default async function PreviewExperiencePage({ params }: { params: Params }) {
  const { experienceId } = await params;
  return (
    <main className="admin-main" id="admin-main" tabIndex={-1}>
      <ExperiencePreview experienceId={experienceId} />
    </main>
  );
}

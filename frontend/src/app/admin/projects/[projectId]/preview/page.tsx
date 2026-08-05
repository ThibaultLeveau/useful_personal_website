import type { Metadata } from "next";

import { ProjectPreview } from "@/features/projects/admin/project-preview";

export const metadata: Metadata = {
  robots: { follow: false, index: false },
};

export default async function PreviewProjectPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  return (
    <main className="admin-main" id="admin-main" tabIndex={-1}>
      <ProjectPreview projectId={(await params).projectId} />
    </main>
  );
}

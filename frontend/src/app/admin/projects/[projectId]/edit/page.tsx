import { ProjectEditor } from "@/features/projects/admin/project-editor";

export default async function EditProjectPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  return (
    <main className="admin-main" id="admin-main" tabIndex={-1}>
      <ProjectEditor projectId={(await params).projectId} />
    </main>
  );
}

import { ProjectEditor } from "@/features/projects/admin/project-editor";

export default function NewProjectPage() {
  return (
    <main className="admin-main" id="admin-main" tabIndex={-1}>
      <ProjectEditor />
    </main>
  );
}

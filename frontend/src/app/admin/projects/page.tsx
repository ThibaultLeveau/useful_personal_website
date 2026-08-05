import { ProjectManager } from "@/features/projects/admin/project-manager";

export default function AdminProjectsPage() {
  return (
    <main className="admin-main" id="admin-main" tabIndex={-1}>
      <ProjectManager />
    </main>
  );
}

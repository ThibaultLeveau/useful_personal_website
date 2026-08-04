import { ExperienceManager } from "@/features/experiences/admin/experience-manager";

export default function AdminExperiencesPage() {
  return (
    <main className="admin-main" id="admin-main" tabIndex={-1}>
      <ExperienceManager />
    </main>
  );
}

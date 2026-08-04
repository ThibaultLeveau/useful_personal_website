import { SkillsManager } from "@/features/skills/skills-manager";

export default function AdminSkillsPage() {
  return (
    <main className="admin-main" id="admin-main" tabIndex={-1}>
      <SkillsManager />
    </main>
  );
}

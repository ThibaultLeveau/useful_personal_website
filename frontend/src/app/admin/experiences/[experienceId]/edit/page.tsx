import { ExperienceEditor } from "@/features/experiences/admin/experience-editor";

type Params = Promise<{ experienceId: string }>;

export default async function EditExperiencePage({ params }: { params: Params }) {
  const { experienceId } = await params;
  return (
    <main className="admin-main" id="admin-main" tabIndex={-1}>
      <ExperienceEditor experienceId={experienceId} />
    </main>
  );
}

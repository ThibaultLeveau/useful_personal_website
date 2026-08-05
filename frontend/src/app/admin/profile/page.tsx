import { ProfileEditor } from "@/features/site-configuration/profile-editor";

export default function AdminProfilePage() {
  return (
    <main className="admin-main" id="admin-main" tabIndex={-1}>
      <ProfileEditor />
    </main>
  );
}

import { SettingsEditor } from "@/features/site-configuration/settings-editor";

export default function AdminSettingsPage() {
  return (
    <main className="admin-main" id="admin-main" tabIndex={-1}>
      <SettingsEditor />
    </main>
  );
}

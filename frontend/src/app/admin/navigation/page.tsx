import { NavigationEditor } from "@/features/site-configuration/navigation-editor";

export default function AdminNavigationPage() {
  return (
    <main className="admin-main" id="admin-main" tabIndex={-1}>
      <NavigationEditor />
    </main>
  );
}

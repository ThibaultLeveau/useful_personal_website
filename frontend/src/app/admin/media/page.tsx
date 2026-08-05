import { MediaLibrary } from "@/features/media/media-library";

export default function AdminMediaPage() {
  return (
    <main className="admin-main" id="admin-main" tabIndex={-1}>
      <MediaLibrary />
    </main>
  );
}

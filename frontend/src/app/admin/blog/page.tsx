import { BlogManager } from "@/features/blog/admin/blog-manager";

export default function AdminBlogPage() {
  return (
    <main className="admin-main" id="admin-main" tabIndex={-1}>
      <BlogManager />
    </main>
  );
}

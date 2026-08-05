import { BlogEditor } from "@/features/blog/admin/blog-editor";

export default function NewBlogPostPage() {
  return (
    <main className="admin-main" id="admin-main" tabIndex={-1}>
      <BlogEditor />
    </main>
  );
}

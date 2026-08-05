import { BlogEditor } from "@/features/blog/admin/blog-editor";

export default async function EditBlogPostPage({
  params,
}: {
  params: Promise<{ postId: string }>;
}) {
  return (
    <main className="admin-main" id="admin-main" tabIndex={-1}>
      <BlogEditor postId={(await params).postId} />
    </main>
  );
}

import { PageEditor } from "@/features/pages/admin/page-editor";
export default async function PageBuilderRoute({
  params,
}: {
  params: Promise<{ pageId: string }>;
}) {
  return <PageEditor pageId={(await params).pageId} />;
}

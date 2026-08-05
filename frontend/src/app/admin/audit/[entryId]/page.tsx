import { AuditDetail } from "@/features/audit";

export default async function AuditDetailPage({
  params,
}: {
  params: Promise<{ entryId: string }>;
}) {
  const { entryId } = await params;
  return (
    <main className="admin-main" id="admin-main" tabIndex={-1}>
      <AuditDetail id={entryId} />
    </main>
  );
}

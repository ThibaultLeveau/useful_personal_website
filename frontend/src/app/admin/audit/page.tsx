import { AuditViewer } from "@/features/audit";

export default function AdminAuditPage() {
  return (
    <main className="admin-main" id="admin-main" tabIndex={-1}>
      <AuditViewer />
    </main>
  );
}

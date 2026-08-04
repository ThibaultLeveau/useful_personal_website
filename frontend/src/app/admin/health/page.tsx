import { HealthPanel } from "@/features/health";

export default function AdminHealthPage() {
  return (
    <main className="admin-main" id="admin-main" tabIndex={-1}>
      <header className="admin-page-header">
        <div>
          <p className="eyebrow">Workspace / Health</p>
          <h1>Application health</h1>
          <p>
            Review the safe deployment summary and dependency readiness without exposing
            infrastructure details.
          </p>
        </div>
      </header>
      <HealthPanel />
    </main>
  );
}

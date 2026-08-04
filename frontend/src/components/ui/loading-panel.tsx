export function LoadingPanel({ label = "Loading page" }: { label?: string }) {
  return (
    <section className="loading-panel" aria-busy="true" aria-live="polite">
      <p className="visually-hidden">{label}</p>
      <div className="loading-panel__skeleton" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
    </section>
  );
}

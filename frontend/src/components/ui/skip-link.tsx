export function SkipLink({ href, label }: { href: `#${string}`; label: string }) {
  return (
    <a className="skip-link" href={href}>
      {label}
    </a>
  );
}

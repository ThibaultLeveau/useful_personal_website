import { useId, type ReactNode } from "react";

import { Surface } from "@/components/ui/surface";

export interface EmptyStateProps {
  action?: ReactNode;
  description: string;
  eyebrow?: string;
  title: string;
}

export function EmptyState({ action, description, eyebrow, title }: EmptyStateProps) {
  const headingId = useId();

  return (
    <Surface className="empty-state" role="region" aria-labelledby={headingId}>
      {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
      <h1 className="empty-state__title" id={headingId}>
        {title}
      </h1>
      <p className="empty-state__description">{description}</p>
      {action ? <div className="empty-state__action">{action}</div> : null}
    </Surface>
  );
}

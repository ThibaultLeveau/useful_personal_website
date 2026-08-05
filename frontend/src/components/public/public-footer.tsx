import type { Route } from "next";
import Link from "next/link";

import { ThemeSelector } from "@/components/ui/theme-selector";
import { LinkTarget, type PublicFooterData } from "@/generated/api/src/models";

export function PublicFooter({
  brand,
  footer,
}: {
  brand?: string | null;
  footer: PublicFooterData;
}) {
  return (
    <footer className="public-footer">
      <div className="public-footer__identity">
        {brand ? <p className="eyebrow">{brand}</p> : null}
        {footer.copyrightText ? <p>{footer.copyrightText}</p> : null}
      </div>
      {footer.columns.map((column, columnIndex) => (
        <section
          aria-labelledby={`footer-column-${columnIndex}`}
          key={`${column.title}-${columnIndex}`}
        >
          <h2 id={`footer-column-${columnIndex}`}>{column.title}</h2>
          <ul>
            {column.items.map((item) => {
              const newWindow = item.target === LinkTarget.NewWindow;
              const properties = {
                href: item.href,
                ...(newWindow ? { rel: "noopener noreferrer", target: "_blank" } : {}),
              };
              return (
                <li key={`${item.label}-${item.href}`}>
                  {item.href.startsWith("https://") ? (
                    <a {...properties}>{item.label}</a>
                  ) : (
                    <Link {...properties} href={item.href as Route}>
                      {item.label}
                    </Link>
                  )}
                </li>
              );
            })}
          </ul>
        </section>
      ))}
      <div className="public-footer__actions">
        <ThemeSelector compact />
      </div>
    </footer>
  );
}

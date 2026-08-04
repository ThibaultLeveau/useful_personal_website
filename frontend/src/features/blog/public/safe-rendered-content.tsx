import type { SafeRenderedContentData } from "@/generated/api/src/models";

import styles from "./blog.module.css";

/**
 * The sole blog HTML sink. Its input is deliberately the generated server-safe DTO,
 * never a source string or an ad-hoc object assembled by a feature component.
 */
function normalizeHeadingFloor(html: string, floor: number): string {
  const levels = [...html.matchAll(/<h([1-6])(?:\s|>)/giu)].map((match) => Number(match[1]));
  if (!levels.length) return html;
  const offset = floor - Math.min(...levels);
  if (offset === 0) return html;
  return html.replace(/<(\/?)h([1-6])(?=\s|>)/giu, (_match, closing: string, value: string) => {
    const level = Math.min(6, Math.max(floor, Number(value) + offset));
    return `<${closing}h${level}`;
  });
}

export function SafeRenderedContent({
  content,
  headingFloor,
}: {
  content: SafeRenderedContentData;
  headingFloor?: number;
}) {
  const html = headingFloor ? normalizeHeadingFloor(content.html, headingFloor) : content.html;
  return (
    <div
      className={styles.prose}
      data-content-policy={`${content.policyName}@${content.policyVersion}`}
      data-source-checksum={content.sourceChecksum}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

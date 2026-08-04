import { Fragment } from "react";

function inline(value: string) {
  const segments = value.split(/(\[[^\]]+\]\((?:https?:\/\/|\/|#)[^)]+\))/gu);
  return segments.map((segment, index) => {
    const match = /^\[([^\]]+)\]\(((?:https?:\/\/|\/|#)[^)]+)\)$/u.exec(segment);
    if (!match) return <Fragment key={`${segment}-${index}`}>{segment}</Fragment>;
    const label = match[1] ?? "";
    const href = match[2] ?? "#";
    return (
      <a
        href={href}
        key={`${href}-${index}`}
        rel={href.startsWith("http") ? "noreferrer" : undefined}
      >
        {label}
      </a>
    );
  });
}

export function ControlledMarkdown({ value }: { value: string }) {
  const blocks = value.split(/\n{2,}/u).filter(Boolean);
  return (
    <div className="controlled-markdown">
      {blocks.map((block, index) => {
        if (block.startsWith("### ")) return <h3 key={index}>{inline(block.slice(4))}</h3>;
        if (block.startsWith("## ")) return <h2 key={index}>{inline(block.slice(3))}</h2>;
        if (block.startsWith("# ")) return <h2 key={index}>{inline(block.slice(2))}</h2>;
        const lines = block.split("\n");
        if (lines.every((line) => line.startsWith("- "))) {
          return (
            <ul key={index}>
              {lines.map((line) => (
                <li key={line}>{inline(line.slice(2))}</li>
              ))}
            </ul>
          );
        }
        return <p key={index}>{inline(block.replaceAll("\n", " "))}</p>;
      })}
    </div>
  );
}

import type { HTMLAttributes } from "react";

import { classes } from "@/lib/classes";

type SurfaceTone = "default" | "subtle" | "inverse";

export interface SurfaceProps extends HTMLAttributes<HTMLDivElement> {
  tone?: SurfaceTone;
}

export function Surface({ className, tone = "default", ...props }: SurfaceProps) {
  return <div className={classes("surface", `surface--${tone}`, className)} {...props} />;
}

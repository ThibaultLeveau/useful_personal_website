import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import { resolveApiUpstreamOrigin } from "@/lib/api/upstream";

export { resolveApiUpstreamOrigin } from "@/lib/api/upstream";

export function proxy(request: NextRequest) {
  const upstream = new URL(resolveApiUpstreamOrigin());
  upstream.pathname = request.nextUrl.pathname;
  upstream.search = request.nextUrl.search;
  return NextResponse.rewrite(upstream);
}

export const config = {
  matcher: "/api/v1/:path*",
};

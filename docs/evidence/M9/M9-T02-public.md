# M9-T02-P public responsive image evidence

The shared public component renders `<picture>` with WebP sources and fallback `img`, intrinsic width/height,
bounded 320/640/960/1440/1920 `srcset`, owner-specific `sizes`, authored alt/caption, focal positioning, eager
loading only for the profile/LCP candidate, and lazy loading elsewhere. It constructs only application delivery
routes.

Unauthenticated delivery returned `200 image/jpeg` and `200 image/webp` with `public, max-age=300,
s-maxage=300`, `nosniff`, restrictive CSP/frame/resource headers, and no storage data. Unknown assets returned
404. Draft/unpublished page assets returned 404 in PostgreSQL integration and became deliverable only after
publication; unpublish revoked eligibility.

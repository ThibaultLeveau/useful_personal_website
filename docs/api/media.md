# Media API

All administrator operations require an administrator session. Unsafe methods additionally require the
trusted `Origin` and `X-CSRF-Token` conventions. Upload and destructive lifecycle operations accept an
`Idempotency-Key`; metadata changes and deletion use `ETag`/`If-Match`. Exact schemas and operation IDs
are authoritative in [OpenAPI](openapi.json).

## Administrator operations

- `POST /api/v1/admin/media` — multipart upload using the `file` part; returns only after the asset is
  ready or safely failed.
- `GET /api/v1/admin/media` — bounded page/page-size listing with display-name search and closed filters.
- `GET /api/v1/admin/media/{asset_id}` — safe metadata and registered rendition descriptors.
- `PATCH /api/v1/admin/media/{asset_id}` — change the sanitized display name with `If-Match`.
- `GET /api/v1/admin/media/{asset_id}/usage` — authorized owner/role/activity facts.
- `GET /api/v1/admin/media/{asset_id}/content` — authenticated stripped preview selected from registered
  widths and WebP/fallback representations.
- `DELETE /api/v1/admin/media/{asset_id}` — tombstone and remove an unused ready asset; active use returns
  `409 RESOURCE_CONFLICT`.

Multipart bodies are capped before decode. The server validates detected format, dimensions, decoded
pixel count, trailing data, and metadata policy; it never trusts the client MIME type or extension.
Stable failures include `UNSUPPORTED_MEDIA_TYPE`, `PAYLOAD_TOO_LARGE`, `VALIDATION_ERROR`,
`RESOURCE_CONFLICT`, and not-found parity.

## Public delivery

`GET /api/v1/media/{asset_id}/{width}?representation=webp|fallback` is unauthenticated but deny-by-default.
It returns only a registered stripped variant when an exact active use still matches a currently public
owner pointer. Draft, hidden, future, unpublished, deleted, unknown, original, and quarantine content all
have not-found behavior. Successful responses declare the real image content type, `nosniff`, restrictive
security headers, and `Cache-Control: public, max-age=300, s-maxage=300`.

Clients must use only widths supplied by the public responsive descriptor. Storage backend, bucket,
endpoint, object key, checksum, credential, and original-object information are never public API fields.

```console
curl --fail --silent --show-error \
  "https://site.example/api/v1/media/01900000-0000-7000-8000-000000000001/960?representation=webp" \
  --output image.webp
```

The example identifier and host are synthetic. Administrator curl examples intentionally omit session and
CSRF material; do not place those secrets in documentation or shell history.

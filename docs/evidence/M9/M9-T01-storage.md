# M9-T01-S storage and image-security evidence

The local and S3-compatible adapters implement the same private managed-object port: bounded quarantine write, immutable put, promote, read, stat/checksum, idempotent delete, and prefix-confined listing. Local paths resolve beneath one absolute private root and reject unregistered keys, traversal, and links. S3 configuration rejects HTTP, incomplete encryption, missing ownership decisions, and provider defaults.

Pillow 12.3.0 validates exact JPEG/PNG/WebP containers, MIME agreement, one frame, dimensions, pixels, and processing timeout/concurrency. It strips metadata by decoding and re-encoding every delivery variant. Focused storage tests passed traversal/key isolation, cap cleanup, immutable overwrite rejection, promotion, checksums, list/delete parity, SVG/polyglot/MIME mismatch rejection, and stripped responsive output.

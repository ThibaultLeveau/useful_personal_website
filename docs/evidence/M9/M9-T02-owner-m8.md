# M9-T02-O8 page/block owner activation

Image and image-with-text blocks now require a real ready media ID through the shared picker. Save derives one
canonical page-block usage with authored alt, caption, focal coordinates, position, and public intent. Public
eligibility rechecks the exact visible block, frozen published revision, current page pointer, schedule, and
visibility.

Browser acceptance created a custom page, selected a ready image, published it, and rendered the stripped
responsive asset. Review found and fixed an in-place edit failure: SQLAlchemy now flushes deletion of the old
unique block reference before inserting its replacement. A dedicated PostgreSQL regression proves alt,
caption, and focal metadata can be replaced without a uniqueness failure.

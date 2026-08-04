# M9-T02-O3 profile and website owner activation

Profile image plus website logo, favicon, and social-image fields validate ready assets and replace canonical
owner usages inside the same optimistic transaction as the owner save. Profile browser acceptance selected a
ready asset, saved it, rendered a public responsive portrait, reported `profile / profile image · Active ·
Public`, and disabled deletion. PostgreSQL API integration covers profile/settings persistence, public
allow-listing, validation, concurrency, and usage lifecycle.

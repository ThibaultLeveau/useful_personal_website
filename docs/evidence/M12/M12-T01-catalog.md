# M12 event catalog and redaction

Date: 2026-08-04

The frozen schema-version-one catalog contains 79 exact identifiers spanning authentication/security, API tokens, profile/settings/navigation/footer, skills, experiences, projects, blog, pages, media, contacts, demo operations, and audit retention. Every identifier owns an exact metadata-key allow-list. Unknown events, schema versions, metadata keys, unsafe labels/correlation, multiline values, and strings longer than 128 characters fail before persistence and again during projection.

The global forbidden-key corpus covers passwords, secrets/tokens, authorization/cookies/CSRF, contact identity/body, raw IP, storage/connection values, SQL, and stack details. API projections omit the stored HMAC IP pseudonym and expose only the allow-listed safe metadata string map. Focused catalog tests passed, including unknown-event, forbidden-key, multiline, and schema-version negatives.

# Skills API

The canonical schemas and operation IDs are in [OpenAPI](openapi.json). All administrator routes
require a full `AdminSessionCookie`; unsafe methods also require the exact trusted `Origin` and the
session-bound `X-CSRF-Token`. Responses use the common success/error envelopes.

## Routes

| Method                 | Path                                                          | Purpose                                               |
| ---------------------- | ------------------------------------------------------------- | ----------------------------------------------------- |
| `GET`, `POST`          | `/api/v1/admin/skill-categories`                              | List the complete order or append a category          |
| `GET`, `PUT`, `DELETE` | `/api/v1/admin/skill-categories/{category_id}`                | Read, replace, or delete an empty category            |
| `PUT`                  | `/api/v1/admin/skill-categories/actions/reorder`              | Replace the complete category order                   |
| `GET`, `POST`          | `/api/v1/admin/skills`                                        | Filter/page skills or append a skill                  |
| `GET`, `PUT`, `DELETE` | `/api/v1/admin/skills/{skill_id}`                             | Read, replace, or delete a skill                      |
| `PUT`                  | `/api/v1/admin/skill-categories/{category_id}/skills/reorder` | Replace one category's complete order                 |
| `GET`                  | `/api/v1/public/skills`                                       | List only visible skills with public category context |

Create and reorder operations require `Idempotency-Key` (16–128 characters). Updates, deletes, and
reorders require the current strong `If-Match`, such as `"v3"`. Resource reads and writes return the
current `ETag`. Failed commands are atomic and are not stored as successful idempotency outcomes.

## Fields and validation

Category and skill slugs normalize to lowercase ASCII kebab case, are 1–80 characters, and are
globally unique within their resource. Skill score is nullable and otherwise an integer from 0 to 100. `years_experience` is a required exact decimal string from `0` to `999.99`, with at most two
fractional digits; clients must not round it. `icon_key`, when supplied, is lowercase kebab case.

`associated_project_ids` and `associated_experience_ids` currently accept only empty arrays. A
non-empty value returns `VALIDATION_FAILED` with `capability_unavailable`. M5/M6 will consume the
application-facing `SkillReferenceFacade`; there are deliberately no placeholder relation tables or
public links in M4.

## Collection catalog

| Audience      | Filters                                        | Sort fields                                          |
| ------------- | ---------------------------------------------- | ---------------------------------------------------- |
| Administrator | `category_id`, `visible`, `featured`, `search` | `position`, `name`, `created_at`, `updated_at`, `id` |
| Public        | `category`, `featured`, `search`               | `position`, `name`, `featured`, `id`                 |

Both lists accept `page` (default 1), `page_size` (default 20, maximum 100), and one allow-listed
`sort` optionally prefixed with `-`. Unknown, duplicate, bracketed, malformed boolean/UUID, and
non-normalized category inputs return `VALIDATION_FAILED`. Public responses use
`public, max-age=0, s-maxage=60, stale-while-revalidate=300`; administrator responses are private
and `no-store`.

In addition to common errors, a non-empty category delete maps to
`RESOURCE_VERSION_CONFLICT` with safe reason `category_in_use`; duplicate slugs map to a field-level
`VALIDATION_FAILED`; unavailable relation providers map to field-level validation. Unauthorized
reads do not disclose resource existence.

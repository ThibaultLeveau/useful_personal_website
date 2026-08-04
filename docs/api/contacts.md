# Contact API

`GET /api/v1/public/contacts/form-context` issues a short-lived signed completion proof and the deployment-configured policy version. `POST /api/v1/public/contacts` accepts one validated message with `Idempotency-Key`; success is always the disclosure-safe `202 accepted` shape and never returns a contact identifier.

All `/api/v1/admin/contacts` operations require a full administrator session and return `Cache-Control: no-store`. Lists support only state/date filters, explicit oldest/newest sorting, and bounded pagination. Detail reads do not mutate state. State changes and hard deletes require CSRF protection plus `If-Match` optimistic concurrency.

The canonical state machine is `unread → read → archived`, with `archived → read` as the only restore path. There is deliberately no public read/status/search operation and no content search or body preview in the inbox.

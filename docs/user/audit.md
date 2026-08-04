# Review audit activity

Open **Administration → Audit** to inspect security and content-management activity. The newest events appear first. Filter by an exact event, actor type or identifier, resource type or identifier, outcome, UTC date interval, or request ID. Active filter chips can be removed individually, and the complete filter set can be cleared.

Select **View** to open a durable event detail. The detail contains only safe identifiers and the small metadata allow-list defined for that event. Sensitive values are not stored in the audit record, so the interface does not offer payload search or reveal controls.

On narrow screens the table becomes equivalent labeled cards. Pagination remains explicit and no background polling occurs. If the administrator session expires, audit records are removed from the page before the secure redirect.

The audit interface is read-only. It cannot change or delete events, export data, inspect logs, restart services, change configuration, or run retention.

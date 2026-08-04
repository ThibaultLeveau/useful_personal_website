# Manage API tokens

Open **Administration → API tokens**. Give each integration a descriptive name, select only the scopes it needs, and normally keep the 90-day expiry. No-expiry credentials require an explicit risk confirmation.

The complete token appears once after creation or rotation. Copy it directly into the integration’s secret manager, then close the reveal panel. The site cannot recover it later. Never paste tokens into URLs, screenshots, support messages, source control, or browser storage.

Rotation immediately revokes the previous secret and reveals a replacement once. Revocation is also immediate. Use the inventory’s status, expiry, suffix, and last-used time to identify credentials without exposing them.

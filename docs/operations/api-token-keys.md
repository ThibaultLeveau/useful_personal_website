# API token key operations

Tokens use HMAC-SHA-256 with a purpose-separated deployment pepper; only the digest and non-secret key-version identifier are stored. Production requires `APP_TOKEN_DIGEST_PEPPER` with at least 32 unpredictable bytes and a non-development `APP_TOKEN_DIGEST_KEY_VERSION` owned by the secret-management process.

The current runtime accepts only its configured key version. A planned rotation therefore requires: deploy code/config capable of the approved active/previous lookup, verify restored backups can resolve the recorded version, rotate or revoke active credentials, remove the previous key only after the inventory is clear, and record an aggregate audit result. Never print either pepper.

Emergency response is to revoke affected token rows, rotate the pepper under incident control, and require new one-time credentials. Restored databases remain unusable for token authentication unless the corresponding key version is available, which is intentional fail-closed behavior.

Authentication has separate PostgreSQL 15-minute policies: 30 attempts per selector for malformed/unknown credentials and 600 successful-digest attempts per selector. These do not share login or contact buckets. Edge throttling remains required for volumetric protection.

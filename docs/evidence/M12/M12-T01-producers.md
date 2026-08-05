# M12 producer coverage

Date: 2026-08-04

The catalog reconciles the event families emitted by M1-M11 application services: administrator bootstrap/login/logout/password actions; profile/settings/navigation/footer mutations; skill, experience, project, blog, and page lifecycles; media upload/update/delete/failure; private contact submission/transitions/deletion; API-token create/use/rotate/revoke; and explicit demo seeding. Existing producers continue to append through their caller-owned unit of work, so business mutations and successful audit records share the transaction where feasible. Failed authentication and media failure retain their established bounded short transactions.

No producer accepts arbitrary audit JSON. Repository insertion now performs the catalog validation for all database-backed producers. The complete 321-test backend suite passed after the enforcement was installed.

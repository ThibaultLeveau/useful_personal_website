# M12 schema decision

Date: 2026-08-04

Existing audit indexes already satisfy the frozen list predicates: occurrence/ID, event/time, actor/time, resource/time, and exact request ID. The append-only table, metadata-object and actor/outcome/schema constraints also remain sufficient, so no table or index change was justified.

One successor migration was required solely because unconditional M1 mutation prevention made an operator retention capability impossible. Revision `20260802_0013` replaces that trigger function with a guarded retention-only delete path and adds a non-public bounded security-definer function. It adds no table, mutable field, health storage, export payload, or speculative index. `0013 → 0012 → 0013` passed, and `0013` is the sole current head.

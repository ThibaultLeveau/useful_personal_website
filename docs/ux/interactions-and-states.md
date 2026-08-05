# Interactions and States

## Action hierarchy

- One visible primary action per region. Save draft is primary while editing; Publish is a distinct reviewed transition, not a synonym for Save.
- Row click may open detail only if the row also contains a visible named link. Nested buttons do not trigger row navigation.
- Safe, reversible mutations may be optimistic only with immediate rollback and announcement: mark read/unread, archive/restore, visibility, and local reorder. Create, publish, unpublish, delete, token operations, password changes, uploads, and settings saves wait for server confirmation.
- `Cmd/Ctrl+K` opens admin commands; `/` focuses list search; `Esc` closes the topmost transient surface; shortcuts are disabled while typing and are documented in the command menu.

## Async state matrix

| State | Required presentation |
|---|---|
| Initial | Stable shell, title, and context; no flash of privileged/stale content |
| Loading | Geometry-matched skeleton or inline progress; one polite status announcement; preserve navigation |
| Success | Updated content plus inline saved/status indicator; toast only as secondary confirmation |
| Empty collection | Explain what belongs here and offer one permitted create/learn action |
| No filter result | Preserve query/filters; show result count zero and `Clear filters` |
| Validation error | Focused summary plus linked inline errors; retain input; stable machine code stays in diagnostics, not primary copy |
| Server error | Safe explanation, Retry when idempotent, request ID, and alternate navigation; never stack traces |
| Unauthorized/expired | Remove protected DOM/cache, announce expiry, redirect to safe login/expired screen with validated local return path |
| Offline | Mark current content as potentially stale; queue nothing unless an explicit safe offline contract exists |
| Version conflict | Preserve local draft, show latest-change conflict, offer reload/review/copy; never overwrite silently |

## Forms and saving

- Persistent labels; required/optional status declared once. Validate locally on blur, then server on submit. Focus error summary after failed submit.
- Save status is always visible: `Unsaved changes`, `Saving...`, `Saved at {local time}`, or `Save failed`. Do not use color/toast alone.
- Navigation with dirty state opens a three-action dialog: `Stay`, `Leave without saving`, `Save and continue` when the save is valid. Browser unload uses the platform warning as fallback.
- A session-expiry warning appears before idle expiry when feasible and offers Continue session if backend policy supports it; otherwise Save and re-authenticate. Never promise saved work before the server confirms.
- Scheduled dates show configured timezone next to the input, local preview, and UTC in supplementary detail. Reject ambiguous/nonexistent local times explicitly.

## Publication and preview

Lifecycle and visibility appear together:

| Condition | Label | Available primary transition |
|---|---|---|
| No published revision | Draft | Preview, Publish |
| Future effective revision | Scheduled for {date/time} | Preview, Reschedule, Unpublish |
| Effective + visible | Published | View live, Unpublish |
| Effective + hidden | Published + Hidden | Show publicly or Unpublish |
| Live revision differs from draft | Published - changes pending | Preview draft, Publish changes |
| Published pointer cleared | Unpublished | Preview, Republish |

Publish review lists missing/invalid references and blocks confirmation until release-critical issues resolve. Preview uses the draft revision, shows a non-dismissible banner, opens in a new tab or full-screen surface, uses private/no-store responses, and never offers a public share link. Unpublish explains immediate route impact. Delete is separate and does not masquerade as unpublish.

Traceability: F1-011, F2-005-F2-007, F2-012; AC-011, AC-020.

## Block editing and reordering

- Selecting a block synchronizes outline and inspector; focus does not jump merely because selection changed by pointer.
- Drag handle is the only drag origin. Keyboard sequence: focus handle, Space to lift, arrows to move, Space to drop, Esc to cancel. Also expose Move up/down and Move to position.
- Announce `Moved {block name} to position {n} of {total}`. Preserve scroll and selected block after server save.
- Hide is reversible and immediate in preview; duplicate creates an independent block ID; delete asks confirmation and offers a short undo only if undo is genuinely transactional.
- Schema errors appear in outline issue count and inspector fields. Unknown type/version is read-only with an explicit migration/support error; raw JSON is never editable.

## Destructive and security-sensitive actions

| Action | Confirmation rule |
|---|---|
| Delete unused draft/block/skill | Named confirmation; explain relationship effects; no typed phrase unless blast radius is high |
| Delete page/project/post/experience | Name, public-route effect, relation impact; require typing the item name when published or widely referenced |
| Delete media | First query usage; block if referenced with usage links; unused asset gets explicit irreversible confirmation |
| Delete contact | Permanent-delete dialog with subject/date, privacy consequence, and explicit checkbox/confirm; never echo body/email |
| Unpublish | Confirm immediate public removal; not framed as data deletion |
| Revoke token | Name/public suffix and immediate integration impact |
| Rotate token | State old secret is revoked atomically; then use one-time reveal |
| Change password | Confirm other-session revocation; require current password unless forced setup contract differs |

Danger dialogs autofocus the heading or least destructive action, never Delete. Escape/cancel closes; focus returns to invoker.

## One-time token reveal

The creation/rotation result is a modal with the secret in a read-only field, Copy button, plain-language one-time warning, safe token name/scopes/expiry, and `I have stored this token` acknowledgment before Close. Copy success is announced inline; copy failure leaves the secret selectable. Closing permanently removes the secret from component/query state and browser history. No toast, URL, log, audit detail, or later list contains it (F2-016-F2-017, SEC-008 / AC-023).

## Contact handling

Inbox defaults to unread/newest. Loading detail does not mark read until content succeeds. Archive is reversible; restore returns to Read. Permanent deletion clears cached detail and focuses the next row/list heading. Notifications use submission ID/subject/date only where safe, never email/body. A session-expiry event immediately removes private detail from view (F2-008-F2-009, SEC-009 / AC-018, AC-024).

## Feedback, focus, and motion

- Toasts announce noncritical results politely and remain at least 5 seconds or until dismissed; critical errors stay inline.
- After create, focus the new screen heading. After delete, focus the next logical record/list heading. After pagination, focus results heading. Dialog/drawer close restores the invoker.
- Use polite live regions for save, copy, reorder, result count, and upload progress; assertive only for blocking errors/time-critical expiry.
- Reduced motion uses instant state changes; no parallax, shimmer, animated counters, or forced smooth scroll.

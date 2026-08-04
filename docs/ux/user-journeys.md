# User Journeys

## Journey notation

Each journey names the desired outcome, normal path, recovery path, and requirement evidence. A product test should preserve the same conceptual steps even if responsive presentation changes.

## J1 - Visitor evaluates credibility and makes contact

**Outcome:** understand expertise through evidence and submit a private inquiry.

1. Visitor lands on Home and can skip directly to main content.
2. Hero names the role and value proposition; featured skills, experiences, projects, and writing provide evidence rather than unsupported claims.
3. Visitor opens a project, scans problem/solution/impact, inspects screenshots and related skills, then follows a clear Contact action.
4. Contact explains what data is collected and links to Privacy near the consent control.
5. Visitor completes labeled fields; errors appear inline and in an error summary without clearing input.
6. On success, the form is replaced by a confirmation with an explicit next action. Refresh/back does not create a second submission.

Recovery: unknown or no-longer-public projects produce the same designed not-found page; a contact rate limit explains when to retry without echoing message content; spam classification may return generic success by policy.

Traceability: F1-001, F1-007, F1-010, F1-013; AC-001, AC-007, AC-010, AC-013.

## J2 - Reader finds and reads an article

1. Visitor opens Blog, filters by category/tag, and sees active filters plus result count.
2. Pagination changes the URL and moves focus to the results heading after navigation.
3. Visitor opens a post and receives title, publication date, reading time, safe article structure, code/table overflow handling, and related posts.
4. Future-dated, draft, hidden, or unpublished posts resolve as not found publicly and never enter metadata or recommendations.

Empty collection and no-match states are different: the first invites the owner to publish only in admin; public copy simply offers Projects/About. The second preserves filters and offers `Clear filters`.

Traceability: F1-011-F1-012, API-004-API-005; AC-011-AC-012, AC-029.

## J3 - Initial administrator setup and forced password change

1. Operator performs the explicit bootstrap outside the UI. No setup screen appears unless the approved bootstrap mechanism makes it available.
2. Administrator logs in with the initial credential. Error copy is identical for unknown email and wrong password.
3. The server flags `must_change_password`; all ordinary admin routes redirect to the focused password-change step.
4. Password requirements are visible before entry. Paste, password managers, and reveal controls work.
5. Successful change revokes other sessions, shows confirmation, and enters the dashboard (or asks for a fresh login if the backend policy requires it).

Recovery: throttling communicates a retry window; an expired setup session returns to Login without preserving credential fields; bootstrap replay never offers takeover.

Traceability: F2-001-F2-002, SEC-002-SEC-003, NFR-002; AC-015-AC-016, AC-032.

## J4 - Create, preview, schedule, publish, edit, and unpublish content

Applies to pages, experiences, projects, and posts.

1. Administrator creates an entity; the editor begins in `Draft` with required-field guidance.
2. They save explicitly. Server validation maps to fields; the first invalid field receives focus from the summary.
3. `Preview` saves or asks to save, then opens authenticated preview with a persistent `Draft preview - not public` banner. Preview is not shareable outside the session.
4. `Publish` opens a review dialog containing lifecycle effect, visibility state, unresolved warnings, and `Now` or future date/time in configured timezone.
5. Publishing freezes a consistent revision. A future time produces `Scheduled`; current time produces `Published` if visible.
6. Editing a published entity creates/updates a separate draft. UI shows `Published - changes pending`, with links to view Live and Preview draft.
7. Unpublish confirmation explains that the public route will stop resolving while revisions remain. Success moves to `Unpublished`.

Guards: required public references are validated at publish time; `Hidden` is a separate switch and can make a published revision nonpublic; `Featured` never overrides either. Destructive delete is not combined with unpublish.

Conflict recovery: on `RESOURCE_VERSION_CONFLICT`, stop autosubmission, preserve the local form in memory, show `Review latest version`, and offer `Copy my changes` plus reload. Never silently overwrite.

Traceability: F2-005-F2-007, F2-012, API-006; AC-009-AC-011, AC-020, AC-030.

## J5 - Build a page with typed blocks

1. In Page editor, administrator chooses `Add block`; a searchable catalog groups Narrative, Evidence, Media, and Conversion blocks.
2. Selecting a type inserts a draft block after the current selection and opens its schema-specific inspector.
3. The inspector separates Content, References, Appearance, and Responsive settings. Unsupported/unknown options never appear.
4. Administrator reorders blocks by drag handle, keyboard move commands, or explicit Move up/down actions. A live region announces the new position.
5. Hide keeps the block editable but excludes it from public render. Duplicate creates a new ID adjacent to the source. Delete removes only the draft block after confirmation/undo policy.
6. Outline and preview reflect the same order. Save is atomic for the page version.

On touch/mobile, reordering defaults to Move up/down and `Move to position` rather than precision drag. Required references that are missing can be saved in a draft but block publication with a linked issue list.

Traceability: F1-005-F1-006, F2-012-F2-013, NFR-002; AC-005-AC-006, AC-020, AC-032.

## J6 - Upload and reuse media safely

1. Administrator opens Media or invokes the Media picker from an editor.
2. They choose files with a button or drop them; the UI states JPEG/PNG/WebP, 10 MiB, 6000 px/side, and 36 MP limits before selection.
3. Each item shows upload/validation progress independently. A rejected file retains filename plus a safe actionable reason.
4. Successful upload opens metadata; meaningful use requires useful alt text, while decorative use is an explicit per-use choice rather than an empty-alt accident.
5. Picker returns the selected media and its intended usage to the editor.
6. Delete shows usage locations. If in use, deletion is disabled and the user can open each safe usage location. If unused, explicit confirmation deletes it.

Storage/quarantine errors never imply completion. Closing during upload asks for confirmation only when interruption would abandon work.

Traceability: F1-014, F2-010-F2-011, SEC-007; AC-014, AC-019.

## J7 - Create, store, rotate, and revoke an API token

1. Administrator chooses `Create token`, enters a unique descriptive name, selects scopes, and chooses an expiry (90 days recommended; no expiry requires explicit acknowledgment).
2. Review summarizes capabilities in plain language and warns that token administration/password changes/contact deletion are never permitted.
3. Creation returns the secret once in a blocking result dialog with Copy, download-as-text only if approved by security, and `I have stored this token` acknowledgment.
4. After dismissal, the list shows only safe public ID suffix, name, scopes, created/expiry/last-used metadata, and status. There is no Reveal action.
5. Rotate repeats one-time display and states that the old secret is revoked immediately.
6. Revoke requires confirmation naming the token and explains the integration will stop immediately.

Copy feedback is both visual and announced; failure selects the field for manual copy. The secret never appears in URL, toast, audit detail, list DOM after close, or analytics.

Traceability: F2-016-F2-017, API-008, SEC-008; AC-023.

## J8 - Triage and remove a contact submission

1. Administrator opens Inbox; default view prioritizes unread, newest first, without showing the message body in table previews or URLs.
2. Opening a submission marks it read only after the detail has loaded. Sender, subject, timestamp, consent policy, and message are clearly separated.
3. Archive is the normal action and is reversible through Archived -> Restore to read.
4. `Delete permanently` opens a high-friction dialog that names the submission by safe subject/date, explains irreversibility and audit behavior, and requires explicit confirmation.
5. After deletion, focus returns to the next list row or list heading; private content is removed from client state.

Session expiry immediately clears detail content and navigates to the safe expired-session screen. Contact email/body never appears in notifications or audit metadata.

Traceability: F2-008-F2-009, SEC-009; AC-018, AC-024.

## J9 - Diagnose health without exposing infrastructure

1. Administrator opens Health and sees `Operational`, `Degraded`, `Unavailable`, or `Unknown`, last-checked time, safe build version, and separate application/database readiness concepts.
2. Manual refresh disables only the refresh control, retains the prior result as `stale`, and announces the new result.
3. A database outage explains that content operations may fail, provides a request ID/docs path, and never prints hostnames, connection strings, SQL, or stack traces.

Traceability: F2-020, API-007; AC-026.

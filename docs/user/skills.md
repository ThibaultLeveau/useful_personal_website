# Skills catalog

The public skills page at `/skills` shows only published skills, grouped in the administrator's
category order. Visitors can search by skill name, choose a category, or show featured skills.
Filters are encoded in the URL, so a filtered view can be bookmarked or shared. A category with no
published matches is omitted. Hidden skills never appear in the public API, page, counts, or
accessibility tree.

## Manage categories

Open **Skills** in the administrator workspace. Create a category with a name, normalized slug, and
optional description. Slugs use lowercase ASCII words separated by hyphens and are unique across
categories. Use **Move up** and **Move down** to save the complete category order. A category must be
empty before it can be deleted.

## Manage skills

Create or edit a skill with its category, name, unique slug, years of experience, optional
description, proficiency label, score from 0 through 100, and icon key. Years are exact decimal
values from `0` through `999.99` with at most two decimal places. **Published** controls anonymous
visibility; **Featured** changes presentation but never overrides a hidden state.

The category selector can reassign a skill. Ordering controls are enabled only on the unfiltered,
complete position view, so a partial page cannot accidentally overwrite items it does not contain.
Editing and deletion remain available while filtering. Deleting a skill closes its category's order
gap.

Project and professional-experience relationships are visibly unavailable until their real
providers arrive in M5 and M6. The interface does not invent targets, and the API rejects non-empty
relation writes. Existing fields can be edited normally without those providers.

## Conflicts and recovery

Each edit uses the version that was loaded. If another session writes first, reload current
versions, reconcile the values, and save again. Creation and reorder requests are retry-safe, but
reusing an idempotency key for different content is rejected. Validation and safe conflict messages
contain a request ID for troubleshooting and never expose database details.

# Site configuration

The administrator workspace separates profile privacy, website defaults, primary navigation, and footer structure. Open the relevant section from `/admin`; every read is authenticated and every save uses the version that was loaded.

## Profile and publication choices

Enter private profile values first, then approve each public field separately. An unchecked value is omitted from the public API, rendered HTML, metadata, and new public cache entries. Saving triggers authenticated cache invalidation; if that cannot be confirmed, public pages expire the old projection within one minute.

Use the public checkboxes as publication decisions, not as a preview convenience. Removing a check
removes the value on the next public request while retaining it for later editing. Before publishing
an email address, location, availability statement, résumé, or social profile, confirm that it is
intended for anonymous visitors.

The profile editor accepts one value or preference per line. Social links use `Label | https://destination.example` and accept HTTPS destinations only. Profile and website image fields use the shared ready-media picker and become public only through the saved owner configuration.

## Website settings

Website settings control public identity, locale, IANA timezone, initial theme policy, colors, public contact values, social links, SEO defaults, and an allow-listed public analytics identifier. They never store analytics credentials or inject provider scripts. Logo, favicon, and social images must be selected from ready private-library assets.

Locales use an IETF language tag such as `en` or `fr-FR`; timezones use an IANA name such as
`Europe/Paris`. An analytics identifier is public page metadata for one supported provider. Never
paste an API key, secret, password, connection string, or script into any settings field.

## Navigation and footer

Navigation supports two levels. Internal destinations use registered local paths and always open in the same window; external destinations require HTTPS and may explicitly open in a new window. Visibility controls remove destinations from the public projection. Move controls are keyboard-operable and preserve deterministic sibling order.

Footer columns and links use the same ordering, visibility, destination, and target rules. Link categories describe ordinary, social, or legal destinations; they do not weaken URL validation.

Use the Move up/down controls to reorder with a pointer or keyboard. A child navigation destination
appears immediately after its parent in the public menu. Hide or remove a parent only after checking
the effect on its children. External new-window destinations are announced by normal browser
semantics and receive safe opener isolation.

## Conflicts and unsaved changes

If another session saves the same resource first, the editor keeps local changes and shows a focused conflict summary. Copy the local JSON if useful, reload the current version, reconcile, and save again. Navigating elsewhere with local edits opens a choice to stay, leave without saving, or save and continue. Browser or tab closing also triggers the platform unsaved-changes warning.

Validation errors appear in a linked summary and beside their fields. Follow the summary link,
correct every reported value, and save again; the server never partially applies a failed tree or
settings update.

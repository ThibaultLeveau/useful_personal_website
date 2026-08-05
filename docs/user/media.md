# Manage images

The media library is available at **Administration → Media**. It stores reusable images privately,
creates stripped responsive renditions, and makes a rendition public only while an approved public
profile, setting, project revision, post revision, or page block uses it.

## Upload and find images

Choose **Upload image**, select a JPEG, PNG, or WebP image, and then choose **Upload**. The maximum
file size is 10 MiB; width and height must each be at most 6000 pixels and the decoded image must be
at most 36 megapixels. The server inspects and decodes the bytes, so changing a filename extension
does not make an unsupported file valid. SVG, GIF, audio, video, documents, and archives are rejected.

An image is selectable only after its status is **ready**. Search uses the sanitized display name;
pagination keeps large libraries bounded. A failed row contains a safe failure state and never has a
public rendition.

## Describe and use an image

Select a ready image in the profile, website settings, project, blog, or page editor. Alternative text,
caption, purpose, and focal position belong to that particular use, not to the reusable file. Write alt
text that conveys the image's purpose in context. Do not copy the filename. Use an empty alt only when
the image is genuinely decorative and the editor permits that purpose.

Saving an immediately effective owner such as Profile activates its usage. Revisioned projects, posts,
and pages keep draft and published revisions separate; public delivery begins only when the relevant
revision is published and visible. Unpublishing, hiding, or removing the reference revokes new public
delivery within the documented five-minute cache window.

## Rename, replace, and delete

The inspector can change the safe display name with optimistic version checking. Replacing image
content always means uploading a new immutable asset and deliberately changing each owner reference;
there is no silent global byte replacement.

The Usage section lists safe owner type, role, active state, and public state. **Delete media** is disabled
while any active usage exists. Remove or replace every listed reference first, save/publish as required,
refresh the library, and then delete the unused asset. Deletion is irreversible at the application level.

If the API cannot be reached, keep the original file, refresh once, and use the request ID from the error
when contacting the operator. Do not repeatedly upload after a timeout until the library confirms whether
the idempotent request succeeded.

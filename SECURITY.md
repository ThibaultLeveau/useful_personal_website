# Security Policy

## Supported versions

There is no supported release yet. The repository is in foundation development and must not be treated as production-ready. Supported version ranges and security-fix policy will be published with the first release.

## Reporting a vulnerability

Do **not** disclose suspected vulnerabilities, exploit details, credentials, tokens, personal data, or private logs in a public issue, pull request, discussion, or chat.

A permanent private reporting channel has not yet been configured. Until it is published, open a public issue containing only a request for private security contact—no vulnerability details—and wait for a maintainer to provide a verified private channel. If the repository exposes GitHub's private vulnerability-reporting interface, that interface may be used directly.

Include the following only through the verified private channel:

- affected revision or version;
- concise impact and threat scenario;
- reproducible steps or a minimal proof of concept;
- relevant configuration with secrets removed;
- known mitigations or workarounds; and
- whether disclosure is already public or time-sensitive.

## Handling expectations

Maintainers will acknowledge and triage reports on a best-effort basis until a published response policy exists. Reporters should not test against systems or data they do not own or have explicit permission to use. Do not access, retain, or share personal data while investigating.

Confirmed Critical or High findings block downstream release acceptance until corrected or explicitly handled by the project’s documented security process. Security evidence must be sanitized according to the [delivery evidence template](docs/plan/delivery-evidence-template.md).

CI runs dependency, static application, secret-history, and production-image vulnerability checks as described in the [CI guide](docs/development/ci.md). A scanner failure must not be suppressed or converted to success to merge a change. Scanner logs and uploaded artifacts are evidence surfaces: sanitize them before retention or repository inclusion, and never paste sensitive findings into public pull-request output.

## Security design

The project's control model, trust boundaries, credential rules, and review expectations are documented in the [security architecture](docs/architecture/security-architecture.md). General defects that contain no sensitive security information may use the bug report form.

## Open maintainer decision

Before public contribution or release, maintainers must configure and publish a durable private security contact and response expectations. This file intentionally contains no placeholder email address or unverified contact.

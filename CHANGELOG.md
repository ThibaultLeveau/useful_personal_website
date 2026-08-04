# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Releases are expected to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html) once a public API and release policy are established.

## [Unreleased]

### Added

- Initial product requirements, architecture decisions, UX specification, implementation plan, and delivery dispatch.
- Repository governance and developer-documentation skeleton.
- Revision-safe project case studies with administrator lifecycle/preview, public filtering and
  metadata, typed generated API clients, accessible responsive interfaces, and staged media
  boundaries.
- Revision-safe blog posts with tags/categories/related posts, controlled CommonMark rendering,
  private preview and exact source export, database-time publication lifecycle, public discovery,
  typed generated clients, metadata/JSON-LD/sitemap integration, and responsive accessible UI.
- Secure private media ingestion for JPEG/PNG/WebP, immutable stripped responsive variants, local
  and S3-compatible storage adapters, active usage/deletion protection, reconciliation, an
  administrator library/shared picker, owner activation, and deny-by-default public delivery.
- A consent-bound private contact workflow with signed timing proof, pseudonymous database rate
  limits, exactly-once submission, authenticated inbox lifecycle, audited deletion, and bounded
  dry-run-first retention operations.
- Scoped digest-only API tokens with one-time create/rotate secrets, exact route authorization,
  expiry/revocation, isolated bearer rate limits, safe audit metadata, generated contracts, and an
  accessible administrator lifecycle interface.
- A fail-closed versioned audit catalog, protected exact-filter list/detail API, responsive
  administrator viewer, safe health view, and dry-run-first least-privilege 400-day retention path.
- Release discovery metadata with canonical URLs, robots/sitemap coverage, structured page data,
  an original social-preview asset, a complete administrator capability/onboarding overview, and
  cross-browser responsive accessibility verification.
- A repaired linear M0-M12 migration compatibility contract at revision `20260802_0013`, clean
  schema autogenerate parity, stricter database typing, static media-eligibility SQL, and permanent
  end-to-end contact/audit/scoped-token regression coverage.
- A 544-test clean PostgreSQL qualification suite with zero skips and 85.0018% branch-aware backend
  coverage, including typed port contracts, deterministic demo seeding, closed administrator error
  catalogs, retention safeguards, and private-media adapter failure boundaries.
- Current non-root production images qualified on exact Node 22.23.2/Python 3.12.13 runtimes, with
  zero High/Critical Trivy findings and a clean redacted Gitleaks staged-source scan.
- The canonical MIT License selected by the maintainer for permissive open-source reuse.

### Known limitations

- No application release exists yet.
- Production media acceptance awaits deployment-owner provider, residency, identity, encryption,
  delivery, lifecycle, and coordinated recovery decisions.
- Production contact acceptance awaits approved legal/controller text, exact network topology,
  pseudonym-key rotation ownership, retention approval, and a recorded restore drill.
- Production API-token acceptance awaits owned pepper/key rotation, revoked-row retention,
  external-consumer route approval, load targets, and an emergency revocation/restore drill.
- Production audit acceptance awaits retention/legal approval, dedicated operator secret injection,
  production-shaped load evidence, and the coordinated backup/restore decision.
- M13 release readiness remains blocked on owner legal/operations decisions, manual
  assistive-technology/real-device testing, and production restore ownership. Automated backend,
  exact-runtime, current-image, and secret-scanning gates pass.

Comparison links will be added after the repository origin and first release tag are established.

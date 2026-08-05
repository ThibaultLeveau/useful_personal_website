# Owner production decision record

Date: 2026-08-05
Owner: Thibault Leveau
Status: Accepted for the R1 single-VPS deployment

## Decisions

- Publisher/data controller: Thibault Leveau; public privacy contact:
  `thibault.leveau@gmail.com`.
- Canonical origin: `https://thibault-leveau.com`; plain HTTP redirects to HTTPS.
- Contact enquiries: 365 days, followed by the bounded operator purge. The requested indefinite
  period was not adopted because identifiable personal data needs a purpose-based retention limit.
- Audit entries: seven days, using the dedicated least-privilege retention operator.
- Private media: dedicated local persistent volume on the single Hostinger VPS. This is an explicit
  single-host tradeoff and must move to private S3-compatible storage before horizontal scaling.
- Backup: coordinated PostgreSQL plus media backup every week; RPO seven days, RTO one hour;
  recovery owner Thibault Leveau.
- Monitoring and incidents: email `thibault.leveau@gmail.com`; incident owner Thibault Leveau.
- Analytics: none at launch. Any future built-in analytics requires a separate minimization,
  retention, consent/cookie, and privacy-notice review before activation.
- External error-reporting service: none at launch. Operational failure alerts route by email.

## Privacy basis

The contact form asks for consent and uses submitted data only to review and answer the enquiry. The
notice identifies the controller, data, purpose, retention, recipients, rights, withdrawal route,
CNIL complaint route, hosting context, and absence of automated decision-making.

The retention correction follows the
[CNIL storage-limitation guidance](https://www.cnil.fr/fr/passer-laction/les-durees-de-conservation):
identifiable personal data cannot be kept indefinitely and the controller must select a period based
on the purpose. This is a practical baseline for this deployment, not individualized legal advice.

## Deployment limitation

Acceptance records the intended values; it does not prove that DNS, TLS, Hostinger firewall, email
delivery, scheduled retention, weekly backups, or one-hour restoration are operational. The owner
must execute the Hostinger deployment and recovery checklist before public promotion.

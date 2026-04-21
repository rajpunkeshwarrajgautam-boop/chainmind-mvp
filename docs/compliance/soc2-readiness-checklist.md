# SOC 2 readiness checklist (engineering-oriented)

Use with a compliance lead; this does **not** constitute certification.

- **CC6 Logical access** — RBAC enforced on APIs; periodic access reviews documented.
- **CC7 System operations** — Centralized logs, alerting on error rate / latency SLOs.
- **CC8 Change management** — PR reviews, CI gates, tagged releases, rollback runbooks.
- **A1 Availability** — Health/readiness probes, backups tested, RTO/RPO defined.
- **C1 Confidentiality** — Encryption in transit (TLS), secrets in vault/KMS, key rotation policy.
- **Incident response** — On-call, customer notification templates, tabletop exercises scheduled.

Map each control to evidence (tickets, screenshots, policies) in your GRC tool.

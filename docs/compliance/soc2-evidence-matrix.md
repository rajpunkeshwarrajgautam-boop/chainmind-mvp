# SOC 2 Type II — evidence matrix (template)

Map each Trust Services Criteria (TSC) to **artifacts** your team must collect. Replace bracketed items with links to tickets, PDFs, or screenshots in your GRC tool.

| TSC / theme | Example controls | Evidence you should store |
|-------------|-------------------|---------------------------|
| CC6.1 Logical access | Unique accounts, MFA for prod | IdP MFA policy, sample SSO login logs, access review ticket |
| CC6.2 Registration & deprovisioning | Joiner/mover/leaver | HR ticket + IAM audit export |
| CC6.3 Authentication | Password policy / SSO | OIDC config export (redacted), pen-test summary |
| CC7.1 Detection | Monitoring & alerting | Prometheus/Grafana dashboard URL, alert routing policy |
| CC7.2 Monitoring | Infra & app metrics | `GET /metrics` retention policy, on-call rotation |
| CC7.3 Evaluation | Vuln management | Grype/SBOM workflow output, exception register |
| CC8.1 Change mgmt | PR reviews, CI | Sample merged PR + required reviewers |
| A1.2 Availability | DR / backups | Backup drill record (`docs/runbooks/backup-restore-drill.md`) |

**Auditor engagement:** schedule readiness review → gap remediation → evidence freeze → fieldwork. This repository cannot substitute auditor sign-off.

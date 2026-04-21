# Pilot support and on-call (lightweight)

Minimal support model for early paid pilots.

## Ownership
- Primary owner: `<name>`
- Backup owner: `<name>`
- Escalation channel: `<email/slack/phone>`

## Response targets (pilot)
- Critical outage acknowledgement: `<e.g., 30 minutes during business hours>`
- Non-critical issue first response: `<e.g., 1 business day>`

## Operating steps
1. Confirm issue and impact scope.
2. Log incident timestamp, customer, and affected endpoints.
3. Communicate first update to customer with ETA.
4. Mitigate or rollback.
5. Publish post-incident notes and preventive actions.

## Tooling (simple is fine)
- Alerts: basic uptime + error-rate checks.
- Logging: retain request/error logs.
- Incident log: one shared document/ticket stream.

## References
- `docs/compliance/incident-response-plan-template.md`
- `docs/runbooks/backup-restore-drill.md`

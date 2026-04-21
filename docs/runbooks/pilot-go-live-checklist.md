# Pilot go-live checklist (paid early access)

Use this before charging a pilot customer.

## Positioning and claims
- **Safe claim:** "Paid pilot / early access for selected customers."
- **Avoid claim:** "Enterprise-ready / certified / production SLA."
- Sales demos and SOW language must match these claims.

## 1) Stable hosted deployment (required)
- Deploy the API to a stable hosted environment (not local laptop-only).
- Configure persistent database storage and encrypted backups.
- Verify uptime endpoints: `/health` and `/ready`.
- Run the vertical slice against the **real** base URL (no placeholder host):

  ```bash
  CHAINMIND_BASE_URL=https://api.your-domain.com python scripts/verify_vertical_slice.py --evidence-dir pilot-evidence/deploy-<DATE>
  ```

  On Windows PowerShell:

  ```powershell
  $env:CHAINMIND_BASE_URL = "https://api.your-domain.com"
  python scripts\verify_vertical_slice.py --evidence-dir pilot-evidence\deploy-<DATE>
  ```

  The script writes **redacted** JSON under `--evidence-dir` (`health.json`, `register.json`, `forecast_sample.json`, `forecast_job.json`, `summary.json`). Attach that folder or zip it to your ticket.
- Copy `docs/runbooks/pilot-deployment-evidence-log.md` into your wiki/ticket and fill the table with links to the artifacts above.
- Record environment URL, deploy commit SHA, and operator contact.

## 2) Backup + restore drill (required once before first paid pilot)
- Follow `docs/runbooks/backup-restore-drill.md`.
- Capture evidence:
  - backup artifact ID/location
  - restore start/end time
  - row-count validation results
  - any incident notes and fixes
- Store evidence in your internal ticket/changelog system.

## 3) Support/on-call path (required)
- Assign a primary and backup human contact.
- Create a single escalation channel (email/Slack/phone).
- Define response targets for pilot:
  - critical outage acknowledgement target
  - non-critical support response target
- Keep an incident log and link to `docs/compliance/incident-response-plan-template.md`.

## 4) Contract/SOW language (required)
- Include pilot limitations and beta terms in customer paperwork.
- Reference `docs/legal/pilot-sow-template.md` as the starting template.
- Ensure legal review is complete before signature.

## 5) Stripe cutover (required before first charge)
- Keep scope minimal: one product/price, checkout + webhook happy path.
- Use `docs/legal/stripe-dpa-note.md` for legal and webhook checklist.
- Execute one end-to-end billing test in Stripe:
  1. successful checkout
  2. webhook delivery verified
  3. subscription record updated in app DB
- Only then switch from test mode to live charging.

## Exit criteria
- All five sections above are marked complete with evidence links (use `pilot-deployment-evidence-log.md`).
- At least one successful `verify_vertical_slice.py` run against the **production pilot** base URL with `--evidence-dir` attached.
- Team can honestly sell as "paid pilot / early access" with no enterprise claims.

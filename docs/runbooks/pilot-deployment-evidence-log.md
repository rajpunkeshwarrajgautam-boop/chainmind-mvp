# Pilot deployment evidence log (template)

Copy this file into your ticket/wiki for each pilot environment (e.g. `pilot-evidence-prod-2026-04-21.md`). Replace placeholders in angle brackets.

## Run metadata

| Field | Value |
|------|--------|
| Environment URL | `<https://api.example.com>` |
| Date (UTC) | `<YYYY-MM-DD>` |
| Operator | `<name>` |
| Git commit SHA | `<sha>` |
| Verify command | `CHAINMIND_BASE_URL=<url> python scripts/verify_vertical_slice.py --evidence-dir <path>` |

## 1) Hosted deployment

| Evidence | Link or path |
|---------|----------------|
| `verify` stdout (OK line) | `<paste or attach verify-stdout.txt>` |
| Redacted HTTP artifacts | `<folder from --evidence-dir>` |
| `/health` screenshot or curl | `<attach>` |
| `/ready` response | `<attach>` (note if Redis optional) |
| `/docs` or OpenAPI | `<attach>` |

## 2) Backup + restore drill

| Evidence | Link or path |
|---------|----------------|
| Backup artifact ID / location | `<>` |
| Restore window (start/end UTC) | `<>` |
| Row-count validation | `<>` |
| Drill notes | `<>` |

## 3) Support / on-call

| Evidence | Link or path |
|---------|----------------|
| Primary + backup contacts | `<>` |
| Escalation channel | `<>` |
| Response targets (pilot) | `<>` |

## 4) Contract / SOW

| Evidence | Link or path |
|---------|----------------|
| Signed SOW / order form | `<store outside repo>` |
| Pilot limitations acknowledged | `<>` |

## 5) Stripe (before live charge)

| Evidence | Link or path |
|---------|----------------|
| Test checkout success | `<Stripe dashboard / event IDs>` |
| Webhook delivery log | `<>` |
| `stripe-live-cutover-check` completed | `docs/runbooks/stripe-live-cutover-check.md` |

## Sign-off

- [ ] All rows above filled for this pilot.
- [ ] Positioning matches: paid pilot / early access only (no enterprise SLA claims).

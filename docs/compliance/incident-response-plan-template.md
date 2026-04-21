# Incident response plan (template)

## Severity levels
- **SEV1** — customer data exposure or prod wide outage  
- **SEV2** — partial outage / integrity issue  
- **SEV3** — security event without proven impact  

## Roles
- **Incident commander** — coordinates comms & timeline  
- **Technical lead** — drives mitigation & forensics  
- **Legal/PR** — external messaging  

## Steps
1. Detect & declare (PagerDuty / manual).  
2. Contain — revoke tokens, block IPs, isolate workloads.  
3. Eradicate — patch root cause.  
4. Recover — restore from backups if needed (`backup-restore-drill`).  
5. Post-incident review — blameless doc, action items.  

Attach runbooks for DB failover, key rotation, and customer notification templates.

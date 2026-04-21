# Backup & restore drill (quarterly)

## Objectives
- Prove **RPO/RTO** targets for Postgres and object storage.
- Validate credentials & runbook accuracy.

## Procedure
1. Take automated snapshot (RDS / managed Postgres) or `pg_dump` to encrypted object storage.  
2. Record checksum + location in change ticket.  
3. Restore to **isolated** instance; run `SELECT COUNT(*)` on critical tables vs prod read-replica.  
4. Document elapsed time, anomalies, follow-ups.  
5. Destroy isolated environment & scrub temp credentials.

For uploads stored in S3 with KMS, repeat with object versioning restore.

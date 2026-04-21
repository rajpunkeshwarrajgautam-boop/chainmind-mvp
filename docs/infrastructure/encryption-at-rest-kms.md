# Encryption at rest & KMS

## Managed Postgres (recommended)
- Enable **storage encryption** at cluster creation (AWS RDS, Cloud SQL, Azure Database).  
- Use customer-managed keys (CMK) where contractually required; rotate annually.  
- **Backups** inherit encryption; test restore quarterly (`backup-restore-drill.md`).

## Application uploads
- Default: `BYTEA` in Postgres (inherits disk encryption).  
- Scale-out path: `app/storage/s3_store.py` with **SSE-KMS** (`AWS_KMS_KEY_ID`).  
- Never log raw object keys with PII in plaintext.

## Secrets
- Load `JWT_SECRET`, `OIDC_CLIENT_SECRET`, `STRIPE_SECRET_KEY` from a vault (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault).

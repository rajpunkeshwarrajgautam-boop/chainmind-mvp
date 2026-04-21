# GDPR — Record of Processing Activities (RoPA) template

| Field | Example entry |
|-------|----------------|
| Controller | [Legal entity name] |
| Purpose | Demand forecasting & inventory analytics for B2B customers |
| Categories of data subjects | Employees of customers (planners), customer org identifiers |
| Categories of personal data | Business contact email, auth identifiers (OIDC `sub`), audit IP |
| Recipients | Hosting provider, Stripe (billing), email provider |
| Transfers outside EEA | [Describe SCCs / IDTA] |
| Retention | Forecasts N years; audit logs M months; backups per backup policy |
| Security measures | TLS, encryption at rest (DB + optional S3 KMS), access logging |

Complete with DPO/legal and keep RoPA versioned.

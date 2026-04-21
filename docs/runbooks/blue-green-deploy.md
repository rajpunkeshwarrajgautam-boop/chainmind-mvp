# Blue / green & rolling deploys (Kubernetes)

## Rolling update (default in `deployment.yaml`)
- `maxUnavailable: 0`, `maxSurge: 1` — minimal blast radius.
- Readiness probe must hit `/ready` (DB + Redis).

## Blue/green pattern
1. Deploy **green** `Deployment` with new image tag + distinct label.  
2. Shift `Service` selector to green after smoke tests.  
3. Keep blue for fast rollback (selector flip).

## Post-deploy
- Watch error rate SLO (`docs/infrastructure/slo-alerting-examples.md`).
- Promote feature flags if applicable.

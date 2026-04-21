# Human-in-the-loop forecasting

- **Explainability** — `POST /api/v1/governance/forecasts/{job_id}/explain` stores permutation-based feature importance for the training slice of that job.  
- **Overrides** — `POST /api/v1/governance/forecasts/{job_id}/override` requires a planner/admin user, a rationale, and replaces `result_json` with the adjusted payload (audit logged).

Pair with UI review queues and approval workflows in the product layer.

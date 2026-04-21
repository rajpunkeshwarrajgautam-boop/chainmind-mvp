# SLO & alerting examples

## HTTP availability
- **SLI:** `sum(rate(chainmind_http_requests_total{status!~"5.."}[5m])) / sum(rate(chainmind_http_requests_total[5m]))`  
- **SLO:** 99.9% monthly  
- **Alert:** burn rate > 14x budget for 15m → page on-call.

## Latency
- **SLI:** p95 of `chainmind_http_request_duration_seconds` for route `/api/v1/forecast` < 2s.  
- **Alert:** p95 > 5s for 10m → ticket + Slack.

## Queue depth (Celery)
- Export broker queue length via Redis exporter or Celery Flower metrics.  
- Alert if pending > threshold for sustained window.

Wire to Datadog / Grafana / PagerDuty per your stack.

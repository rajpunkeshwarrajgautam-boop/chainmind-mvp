# API change management

- Public JSON API is versioned under `/api/v1`. Breaking changes require a new prefix (`/api/v2`).
- Deprecations: announce in release notes, keep old behavior for at least one minor version when feasible.
- Release notes: summarize user-visible changes, migrations, and required configuration updates per deploy.

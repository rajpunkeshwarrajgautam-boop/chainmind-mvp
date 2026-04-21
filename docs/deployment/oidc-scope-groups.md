# OIDC: groups and role mapping (fast path)

JWT login remains the default for the API. When you enable OIDC (`OIDC_ISSUER`, `OIDC_CLIENT_ID`, …), set **`OIDC_SCOPE`** so the IdP returns the claim you use for roles.

Examples:

- **Azure AD**: often `openid profile email` plus **optional** `User.Read` or custom scopes; group claims may require [group overage claims](https://learn.microsoft.com/entra/identity/hybrid/connect/how-to-connect-fed-group-claims) or **App roles** emitted in `roles` instead of `groups`. If you use `roles`, set **`OIDC_ROLE_CLAIM=roles`** in env.
- **Okta**: add `groups` to the scope string if your authorization server exposes a `groups` claim for the client.
- **Auth0**: use an Action or Rule to add `groups` / custom claims to the ID token, then align **`OIDC_ROLE_CLAIM`** with that claim name.

`OIDC_ADMIN_GROUPS` is a comma-separated list of group (or role) values mapped to the `admin` role on JIT provision (`OIDC_JIT_PROVISION=true`). There is no separate admin UI for group-to-role mapping in this MVP.

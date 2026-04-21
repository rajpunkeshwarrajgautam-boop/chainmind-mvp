from __future__ import annotations

from dataclasses import dataclass

from app.db.models import User


@dataclass
class AuthContext:
    tenant_id: int
    user: User | None
    auth_method: str  # jwt | api_key | legacy_key

    @property
    def role(self) -> str:
        if self.user:
            return self.user.role
        if self.auth_method == "legacy_key":
            return "admin"
        return "viewer"

    def require_roles(self, *roles: str) -> None:
        from fastapi import HTTPException

        if self.role not in roles and self.role != "admin":
            raise HTTPException(status_code=403, detail="Insufficient role")

from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from typing import Any


class NotificationService:
    def __init__(self, maxlen: int = 200) -> None:
        self._items: deque[dict[str, Any]] = deque(maxlen=maxlen)

    def add(self, title: str, body: str, severity: str = "info") -> dict[str, Any]:
        item = {
            "id": len(self._items) + 1,
            "title": title,
            "body": body,
            "severity": severity,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        self._items.appendleft(item)
        return item

    def list(self, limit: int = 50) -> list[dict[str, Any]]:
        return list(self._items)[:limit]


notification_service = NotificationService()

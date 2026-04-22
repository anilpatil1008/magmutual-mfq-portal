from __future__ import annotations

from repositories.notification_repository import get_notifications


class NotificationService:
    def get_notifications(self, user_id: str):
        return get_notifications(user_id)

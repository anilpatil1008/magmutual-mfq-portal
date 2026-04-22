from __future__ import annotations

from repositories.user_repository import get_user_profile, get_user_roles


class UserService:
    def get_profile(self, user_id: str):
        return get_user_profile(user_id)

    def get_roles(self, user_id: str):
        return get_user_roles(user_id)

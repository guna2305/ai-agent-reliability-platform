from enum import Enum


class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"

    def can_write(self) -> bool:
        return self in {UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER}

    def can_manage(self) -> bool:
        return self in {UserRole.OWNER, UserRole.ADMIN}

    def is_owner(self) -> bool:
        return self == UserRole.OWNER

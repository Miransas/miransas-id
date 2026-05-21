class SessionRevocationReason:
    LOGOUT = "logout"
    LOGOUT_ALL = "logout_all"
    REUSE_DETECTED = "reuse_detected"
    ROTATED = "rotated"
    EXPIRED = "expired"
    ADMIN_DISABLE = "admin_disable"


class AuditAction:
    RANK_CHANGED = "RANK_CHANGED"
    BADGES_UPDATED = "BADGES_UPDATED"
    USER_DISABLED = "USER_DISABLED"
    USER_ENABLED = "USER_ENABLED"

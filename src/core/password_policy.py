_COMMON_PASSWORDS = frozenset([
    "password", "password1", "12345678", "123456789", "qwerty",
    "admin", "letmein", "welcome", "monkey", "dragon", "master",
    "login", "hello", "iloveyou", "sunshine", "princess", "abc123",
    "111111", "mustang",
])

_SPECIAL_CHARS = frozenset("!@#$%^&*()_+-=[]{}|;':\",./<>?~`")


def validate_password_strength(v: str) -> str:
    """Validates password complexity. Raises ValueError listing all failures."""
    issues: list[str] = []
    if not any(c.isdigit() for c in v):
        issues.append("at least one digit")
    if not any(c.isupper() for c in v):
        issues.append("at least one uppercase letter")
    if not any(c.islower() for c in v):
        issues.append("at least one lowercase letter")
    if not any(c in _SPECIAL_CHARS for c in v):
        issues.append("at least one special character (!@#$%^&* …)")
    if v.lower() in _COMMON_PASSWORDS:
        issues.append("must not be a commonly used password")
    if issues:
        raise ValueError("Password requires: " + ", ".join(issues) + ".")
    return v

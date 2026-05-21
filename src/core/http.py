from fastapi import Request

_MAX_UA_LEN = 500


def get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:45]
    return (request.client.host if request.client else None)


def get_user_agent(request: Request) -> str | None:
    ua = request.headers.get("user-agent")
    if ua and len(ua) > _MAX_UA_LEN:
        return ua[:_MAX_UA_LEN]
    return ua

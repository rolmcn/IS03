import math
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from fastapi import Request
from fastapi.responses import HTMLResponse

ATTEMPTS = defaultdict(int)
BLOCKED_UNTIL = {}

LIMIT = 10
BLOCK_TIME = timedelta(minutes=10)


def get_client_ip(request: Request) -> str:
    client = request.client
    return client.host if client and client.host else "127.0.0.1"


def check_post_limit(request: Request) -> HTMLResponse | None:
    ip = get_client_ip(request)
    now = datetime.now(timezone.utc)

    if ip in BLOCKED_UNTIL and now < BLOCKED_UNTIL[ip]:
        remaining_minutes = math.ceil(
            (BLOCKED_UNTIL[ip] - now).total_seconds() / 60
        )
        return HTMLResponse(
            content=f"Per daug bandymų. Bandykite po {remaining_minutes} min.",
            status_code=429
        )

    if ip in BLOCKED_UNTIL and now >= BLOCKED_UNTIL[ip]:
        del BLOCKED_UNTIL[ip]
        ATTEMPTS[ip] = 0

    return None


def register_post_attempt(request: Request) -> None:
    ip = get_client_ip(request)
    now = datetime.now(timezone.utc)

    ATTEMPTS[ip] += 1

    if ATTEMPTS[ip] >= LIMIT:
        BLOCKED_UNTIL[ip] = now + BLOCK_TIME


def reset_attempts(request: Request) -> None:
    ip = get_client_ip(request)
    ATTEMPTS[ip] = 0
    BLOCKED_UNTIL.pop(ip, None)
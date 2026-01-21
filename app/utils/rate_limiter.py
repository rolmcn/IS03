from datetime import datetime, timedelta, timezone
from collections import defaultdict
from fastapi import Request
from fastapi.responses import HTMLResponse

ATTEMPTS = defaultdict(int)
BLOCKED_UNTIL = {}

LIMIT = 10
BLOCK_TIME = timedelta(minutes=10)

def check_post_limit(request: Request) -> HTMLResponse | None:
    """
    Tikrina, ar IP užblokuotas.
    Grąžina HTMLResponse (429), jei blokas, arba None, jei viskas gerai.
    """
    client = request.client
    ip = client.host if client and client.host else "127.0.0.1"
    now = datetime.now(timezone.utc)

    # Jei IP užblokuotas
    if ip in BLOCKED_UNTIL and now < BLOCKED_UNTIL[ip]:
        remaining_minutes = int((BLOCKED_UNTIL[ip] - now).total_seconds() / 60)
        return HTMLResponse(
            content=f"Per daug bandymų. Bandykite po {remaining_minutes} min.",
            status_code=429
        )

    # Jei blokas pasibaigė
    if ip in BLOCKED_UNTIL and now >= BLOCKED_UNTIL[ip]:
        del BLOCKED_UNTIL[ip]
        ATTEMPTS[ip] = 0

    # **NEDIDINAM ATTEMPTS čia!**
    return None

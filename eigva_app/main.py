from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import asyncio

from eigva_app.routers import (

    login,
    logout,
    accessibility_settings,
    queue,
    works,
    customers,
    account,
    forgot_login,
    manual,
    invoice,
)

from eigva_app.core.rate_limiting.rate_limiter import check_post_limit
from eigva_app.utils.cleanup import cleanup_expired_tokens
from eigva_app.core.security.session_helper import session_context
from eigva_app.error import setup_error_handlers

# =========================================================
# Background task – periodinis pending paskyrų valymas
# =========================================================
async def periodic_cleanup(stop_event: asyncio.Event):
    """
    Kas 10 min:
    - suranda pasibaigusius pending naudotojus
    - ištrina juos
    - po trynimo išsiunčia el. laiškus
    """
    while not stop_event.is_set():
        try:
            async with session_context() as session:
                await cleanup_expired_tokens(session)
        except Exception as e:
            print(f"[cleanup task] klaida: {e}")

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=600)
        except asyncio.TimeoutError:
            pass


# =========================================================
# Lifespan (startup / shutdown)
# =========================================================
@asynccontextmanager
async def lifespan(_app: FastAPI):
    stop_event = asyncio.Event()

    # ---------- STARTUP: vienkartinis valymas iš karto ----------
    try:
        async with session_context() as session:
            await cleanup_expired_tokens(session)
    except Exception as e:
        print(f"[startup cleanup] klaida: {e}")

    # ---------- STARTUP: periodinis background task ----------
    cleanup_task = asyncio.create_task(periodic_cleanup(stop_event))

    yield  # eigva_app jau priima užklausas

    # ---------- SHUTDOWN ----------
    stop_event.set()
    await cleanup_task


# =========================================================
# FastAPI eigva_app
# =========================================================
app = FastAPI(lifespan=lifespan)
setup_error_handlers(app)
# =========================================================
# Static files
# =========================================================
app.mount("/static", StaticFiles(directory="eigva_app/static"), name="static")

# =========================================================
# Routers
# =========================================================
app.include_router(login.router)
app.include_router(logout.router)
app.include_router(accessibility_settings.router)
app.include_router(queue.router)
app.include_router(works.router)
app.include_router(customers.router)
app.include_router(account.router)
app.include_router(forgot_login.router)
app.include_router(manual.router)
app.include_router(invoice.router)

# =========================================================
# Global POST rate limiter
# =========================================================
@app.middleware("http")
async def limit_all_post_requests(request: Request, call_next):
    if request.method == "POST":
        response = check_post_limit(request)
        if response is not None:
            return response
    return await call_next(request)
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from app.routers import index, info_pages, login, logout, accessibility_settings, queue_auto, works_auto, customers_auto, account_auto, forgot_login
from app.utils.rate_limiter import check_post_limit

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(index.router)
app.include_router(info_pages.router)
app.include_router(login.router)
app.include_router(logout.router)
app.include_router(accessibility_settings.router)
app.include_router(queue_auto.router)
app.include_router(works_auto.router)
app.include_router(customers_auto.router)
app.include_router(account_auto.router)
app.include_router(forgot_login.router)

@app.middleware("http")
async def limit_all_post_requests(request: Request, call_next):
    if request.method == "POST":
        response = check_post_limit(request)
        if response is not None:
            return response
    return await call_next(request)


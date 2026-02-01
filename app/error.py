from fastapi import Request
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

templates = Jinja2Templates(directory="app/templates")


def setup_error_handlers(app):

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        if exc.status_code == 404:
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error_code": 404,
                    "error_title": "Puslapis nerastas",
                    "countdown": 10
                },
                status_code=404
            )
        raise exc  # kitos HTTP klaidos bus apdorojamos pagal numatytą logiką

    @app.exception_handler(Exception)
    async def internal_exception_handler(request: Request, exc: Exception):
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_code": 500,
                "error_title": "Techninė klaida",
                "countdown": 10
            },
            status_code=500
        )

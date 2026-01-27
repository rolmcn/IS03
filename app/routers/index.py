import httpx
from datetime import datetime, timezone
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError

from app.config import templates, settings, CONTACT_INFO
from app.utils.helpers import read_text_from_file, convert_to_paragraphs
from app.utils.recaptcha import verify_recaptcha
from app.utils.rate_limiter import check_post_limit, ATTEMPTS, BLOCKED_UNTIL, BLOCK_TIME, LIMIT
from app.utils.mail import send_contact_message
from app.models.contact import ContactData
from app.utils.logger import logger
from fastapi_mail.errors import ConnectionErrors

router = APIRouter()
SITE_KEY = settings.SITE_KEY


# =========================
# GET /
# =========================
@router.get("/", response_class=HTMLResponse)
async def index(request: Request, success: int | None = None):
    try:
        raw_text = read_text_from_file("about-us.txt")
        html_text = convert_to_paragraphs(raw_text, CONTACT_INFO)
    except (OSError, UnicodeDecodeError, ValueError):
        logger.exception("Failed to read or convert about-us.txt")
        html_text = "Apie mus informacija šiuo metu nepasiekiama."

    context = {
        "request": request,
        "about_us_html": html_text,
        "site_key": SITE_KEY,
        "email": "",
        "phone": "",
        "error": None,
        "success": "Dėkojame, Jūsų pranešimas išsiųstas!" if success == 1 else None,
        "contact": CONTACT_INFO,
    }

    return templates.TemplateResponse("index.html", context)


# =========================
# POST /
# =========================
@router.post("/", response_class=HTMLResponse)
async def submit_form(
    request: Request,
    email: str = Form(""),
    phone: str = Form(""),
    recaptcha_response: str | None = Form(None, alias="g-recaptcha-response"),
):
    error: str | None = None
    contact: ContactData | None = None
    ip = request.client.host if request.client and request.client.host else "127.0.0.1"

    # Rate limiter
    try:
        rate_error = check_post_limit(request)
        if rate_error:
            return rate_error
    except KeyError:
        logger.exception(f"Rate limiter key error for IP {ip}")

    # ContactData validacija
    try:
        contact = ContactData(email=email, phone=phone)
    except ValidationError as e:
        msg = e.errors()[0]["msg"]
        if msg.startswith("Value error, "):
            msg = msg.replace("Value error, ", "")
        error = msg
        logger.warning(f"Contact form validation failed for IP {ip}: {msg}")

    # reCAPTCHA
    if not error:
        if not recaptcha_response or recaptcha_response.strip() == "":
            error = "Prašome pažymėti, kad nesate robotas"
        else:
            try:
                valid_captcha = await verify_recaptcha(recaptcha_response)
                if not valid_captcha:
                    error = "reCAPTCHA patvirtinimas nepavyko. Bandykite dar kartą."
            except httpx.RequestError:
                logger.exception(f"reCAPTCHA request error for IP {ip}")
                error = "reCAPTCHA patikrinimas nepavyko. Bandykite vėliau."

    # Bandymų skaičiavimas tik klaidoms
    if error:
        ATTEMPTS[ip] += 1
        if ATTEMPTS[ip] > LIMIT:
            BLOCKED_UNTIL[ip] = datetime.now(timezone.utc) + BLOCK_TIME
            ATTEMPTS[ip] = 0
            error = f"Per daug bandymų. Bandykite po {int(BLOCK_TIME.total_seconds() / 60)} min."
        logger.warning(f"Contact form error for IP {ip}: {error}")

    # Laiško siuntimas
    if not error and contact:
        try:
            await send_contact_message(contact.email, contact.phone)
            return RedirectResponse(url="/?success=1#about-us", status_code=303)

        except ConnectionErrors:
            logger.exception("SMTP connection error while sending contact message")
            error = "Nepavyko išsiųsti pranešimo. Bandykite vėliau."

        except RuntimeError:
            logger.exception("Runtime error while sending contact message")
            error = "Vidinė sistemos klaida. Bandykite vėliau."

    context = {
        "request": request,
        "email": email,
        "phone": phone,
        "site_key": SITE_KEY,
        "error": error,
        "success": None,
        "contact": CONTACT_INFO,
    }

    return templates.TemplateResponse("index.html", context)
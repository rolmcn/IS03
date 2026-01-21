import httpx
import traceback
from datetime import datetime, timezone
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi_mail.errors import ConnectionErrors
from pydantic import ValidationError
from app.config import templates, settings, CONTACT_INFO
from app.utils.helpers import read_text_from_file, convert_to_paragraphs
from app.utils.recaptcha import verify_recaptcha
from app.utils.rate_limiter import check_post_limit, ATTEMPTS, BLOCKED_UNTIL, BLOCK_TIME, LIMIT
from app.utils.mail import send_contact_message
from app.models.contact import ContactData

router = APIRouter()
SITE_KEY = settings.SITE_KEY


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, success: int | None = None):
    raw_text = read_text_from_file("about-us.txt")
    html_text = convert_to_paragraphs(raw_text, CONTACT_INFO)

    context = {
        "request": request,
        "about_us_html": html_text,
        "site_key": SITE_KEY,
        "email": "",
        "phone": "",
        "error": None,
        "success": None,
        "contact": CONTACT_INFO
    }

    if success == 1:
        context["success"] = "Dėkojame, Jūsų pranešimas išsiųstas!"

    return templates.TemplateResponse("index.html", context)


@router.post("/", response_class=HTMLResponse)
async def submit_form(
    request: Request,
    email: str = Form(""),
    phone: str = Form(""),
    recaptcha_response: str | None = Form(None, alias="g-recaptcha-response"),
):
    error = None
    contact = None
    ip = request.client.host if request.client and request.client.host else "127.0.0.1"

    # -------------------------------
    # 0️⃣ Rate limiter viršuje – taupo resursus
    # -------------------------------
    rate_error = check_post_limit(request)
    if rate_error:
        return rate_error  # 429, nebėra resursų švaistymo

    # -------------------------------
    # 1️⃣ ContactData validacija
    # -------------------------------
    try:
        contact = ContactData(email=email, phone=phone)
    except ValidationError as e:
        msg = e.errors()[0]["msg"]
        if msg.startswith("Value error, "):
            msg = msg.replace("Value error, ", "")
        error = msg

    # -------------------------------
    # 2️⃣ reCAPTCHA validacija
    # -------------------------------
    if not error:
        if not recaptcha_response or recaptcha_response.strip() == "":
            error = "Prašome pažymėti, kad nesate robotas"
        else:
            try:
                valid_captcha = await verify_recaptcha(recaptcha_response)
                if not valid_captcha:
                    error = "reCAPTCHA patvirtinimas nepavyko. Bandykite dar kartą."
            except httpx.RequestError as e:
                error = "reCAPTCHA patikrinimas nepavyko. Bandykite vėliau."
                print(f"reCAPTCHA request error: {e}")

    # -------------------------------
    # 3️⃣ ATTEMPTS tik klaidoms
    # -------------------------------
    if error:
        ATTEMPTS[ip] += 1
        if ATTEMPTS[ip] > LIMIT:
            BLOCKED_UNTIL[ip] = datetime.now(timezone.utc) + BLOCK_TIME
            ATTEMPTS[ip] = 0
            error = f"Per daug bandymų. Bandykite po {int(BLOCK_TIME.total_seconds()/60)} min."

    # -------------------------------
    # 4️⃣ Siunčiame laišką tik jei nėra klaidų ir contact sukurtas
    # -------------------------------
    if not error and contact:
        try:
            print("DEBUG: Siunčiame kontaktą:", contact)
            await send_contact_message(contact.email, contact.phone)
            return RedirectResponse(url="/?success=1#about-us", status_code=303)
        except Exception as e:
            print("DEBUG: SMTP klaida:")
            traceback.print_exc()  # spausdina pilną stack trace konsolėje
            error = f"Nepavyko išsiųsti pranešimo: {e}"

    # -------------------------------
    # 5️⃣ TemplateResponse tik klaidoms
    # -------------------------------
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

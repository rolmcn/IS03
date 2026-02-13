import httpx
from eigva_app.config import settings

RECAPTCHA_SECRET = settings.SECRET_SITE_KEY

async def verify_recaptcha(token: str) -> bool:
    """Patikrina Google reCAPTCHA token.
    Grąžina True jei patvirtinta, False jei ne arba jei timeout / klaida.
    """
    if not token:
        return False

    payload = {"secret": RECAPTCHA_SECRET, "response": token}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                "https://www.google.com/recaptcha/api/siteverify",
                data=payload
            )
            result = r.json()
            return result.get("success", False)
    except httpx.RequestError:
        return False

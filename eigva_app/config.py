from fastapi_mail import ConnectionConfig
from pydantic_settings import BaseSettings
from fastapi.templating import Jinja2Templates
from decimal import Decimal

class Settings(BaseSettings):
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_FROM_NAME: str
    MAIL_SERVER: str
    MAIL_PORT: int
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool
    USE_CREDENTIALS: bool
    VALIDATE_CERTS: bool

    DATABASE_URL: str

    SECRET_KEY: str

    SITE_KEY: str
    SECRET_SITE_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
)

templates = Jinja2Templates(directory="eigva_app/templates")

CONTACT_INFO = {
    "company_name": "EFF Energy, MB",
    "company_code": "303307025",
    "vat_code": "LT100008690515",
    "bank_name": "AB „Artea“ bankas",
    "current_account": "LT657189900058467892",
    "address": "Nepriklausomybės al. 10-9, 85127 Naujoji Akmenė",
    "phone": "+370 612 41558",
    "email": "info@effenergy.eu"
}

BASE_URL = "http://127.0.0.1:8001" # <-- pakeisti į https://eigva.lt

SMS_PRICE_PER_SMS = Decimal("0.06") # <-- pakeisti į realią su PVM

LICENSE_PRICING = {
    "base_price": 20,
    "min_price": 10,
    "step": 1
}
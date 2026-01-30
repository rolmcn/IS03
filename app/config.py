from fastapi_mail import ConnectionConfig
from pydantic_settings import BaseSettings
from pydantic import Field
from fastapi.templating import Jinja2Templates

class Settings(BaseSettings):
    CONTACT_MAIL_USERNAME: str
    CONTACT_MAIL_PASSWORD: str
    CONTACT_MAIL_FROM: str
    CONTACT_MAIL_FROM_NAME: str
    CONTACT_MAIL_SERVER: str
    CONTACT_MAIL_PORT: int
    CONTACT_MAIL_STARTTLS: bool
    CONTACT_MAIL_SSL_TLS: bool
    CONTACT_USE_CREDENTIALS: bool
    CONTACT_VALIDATE_CERTS: bool

    NOTIFICATION_MAIL_USERNAME: str
    NOTIFICATION_MAIL_PASSWORD: str
    NOTIFICATION_MAIL_FROM: str
    NOTIFICATION_MAIL_FROM_NAME: str
    NOTIFICATION_MAIL_SERVER: str
    NOTIFICATION_MAIL_PORT: int
    NOTIFICATION_MAIL_STARTTLS: bool
    NOTIFICATION_MAIL_SSL_TLS: bool
    NOTIFICATION_USE_CREDENTIALS: bool
    NOTIFICATION_VALIDATE_CERTS: bool

    database_url: str = Field(alias="DATABASE_URL")

    SECRET_KEY: str

    SITE_KEY: str
    SECRET_SITE_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()

contact_conf = ConnectionConfig(
    MAIL_USERNAME=settings.CONTACT_MAIL_USERNAME,
    MAIL_PASSWORD=settings.CONTACT_MAIL_PASSWORD,
    MAIL_FROM=settings.CONTACT_MAIL_FROM,
    MAIL_FROM_NAME=settings.CONTACT_MAIL_FROM_NAME,
    MAIL_SERVER=settings.CONTACT_MAIL_SERVER,
    MAIL_PORT=settings.CONTACT_MAIL_PORT,
    MAIL_STARTTLS=settings.CONTACT_MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.CONTACT_MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.CONTACT_USE_CREDENTIALS,
    VALIDATE_CERTS=settings.CONTACT_VALIDATE_CERTS,
)

notification_conf = ConnectionConfig(
    MAIL_USERNAME=settings.NOTIFICATION_MAIL_USERNAME,
    MAIL_PASSWORD=settings.NOTIFICATION_MAIL_PASSWORD,
    MAIL_FROM=settings.NOTIFICATION_MAIL_FROM,
    MAIL_FROM_NAME=settings.NOTIFICATION_MAIL_FROM_NAME,
    MAIL_SERVER=settings.NOTIFICATION_MAIL_SERVER,
    MAIL_PORT=settings.NOTIFICATION_MAIL_PORT,
    MAIL_STARTTLS=settings.NOTIFICATION_MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.NOTIFICATION_MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.NOTIFICATION_USE_CREDENTIALS,
    VALIDATE_CERTS=settings.NOTIFICATION_VALIDATE_CERTS,
)

templates = Jinja2Templates(directory="app/templates")

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

BASE_URL = "http://127.0.0.1:8000"
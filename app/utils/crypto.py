import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from passlib.context import CryptContext
from app.config import settings

# -------------------------------
# Gauti secret key iš .env
# -------------------------------
raw_secret = base64.b64decode(settings.SECRET_KEY)

if len(raw_secret) != 32:
    raise ValueError(f"SECRET_KEY turi būti tiksliai 32 baitų, dabar: {len(raw_secret)}")

SECRET_KEY = raw_secret  # AES-256 reikalauja 32 baitų

# -------------------------------
# Passlib konfigūracija (bcrypt)
# -------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -------------------------------
# AES-GCM šifravimas / dešifravimas
# -------------------------------
def encrypt_data(plain_text: str) -> str:
    aesgcm = AESGCM(SECRET_KEY)
    nonce = os.urandom(12)  # 12 baitų nonce
    ct = aesgcm.encrypt(nonce, plain_text.encode("utf-8"), None)
    return base64.b64encode(nonce + ct).decode("utf-8")

def decrypt_data(cipher_text_b64: str) -> str:
    data = base64.b64decode(cipher_text_b64)
    nonce, ct = data[:12], data[12:]
    aesgcm = AESGCM(SECRET_KEY)
    return aesgcm.decrypt(nonce, ct, None).decode("utf-8")

# -------------------------------
# Slaptažodžių hash / patikrinimas
# -------------------------------
def hash_password(password: str) -> str:
    """Sugeneruoja bcrypt hash iš slaptažodžio (iki 72 baitų)"""
    password_bytes = password.encode("utf-8")[:72]  # trunkinam iki 72 baitų
    return pwd_context.hash(password_bytes)

def verify_password(password: str, hashed: str) -> bool:
    """Patikrina slaptažodį pagal hash (iki 72 baitų)"""
    password_bytes = password.encode("utf-8")[:72]
    return pwd_context.verify(password_bytes, hashed)

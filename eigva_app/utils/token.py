import secrets
import hashlib
from datetime import datetime, timedelta

# -------------------------------
# Konfigūracija tokeno
# -------------------------------
TOKEN_LENGTH_BYTES = 32          # sugeneruojamas tokenas (32 baitai)
TOKEN_EXPIRATION_HOURS = 24      # tokeno galiojimas valandomis

# -------------------------------
# Funkcija sugeneruoti tokeną ir hash
# -------------------------------
def generate_confirmation_token():
    """
    Sugeneruoja atsitiktinį tokeną ir jo SHA-256 hashą.
    Grąžina:
        token (str) – tikrasis tokenas, kurį siųsime vartotojui
        token_hash (str) – SHA-256 hash, saugomas DB
        expires_at (datetime) – galiojimo laikas (vietinis serverio laikas)
    """
    # sugeneruojame atsitiktinį tokeną
    token = secrets.token_urlsafe(TOKEN_LENGTH_BYTES)

    # sukuriame hash (SHA-256)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    # nustatome galiojimo laiką vietiniu laiku (UTC+2)
    expires_at = datetime.now() + timedelta(hours=TOKEN_EXPIRATION_HOURS)

    return token, token_hash, expires_at

# -------------------------------
# Funkcija patikrinti tokeną
# -------------------------------
def verify_confirmation_token(token: str, token_hash: str) -> bool:
    """
    Patikrina, ar pateiktas tokenas atitinka hash.
    """
    computed_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return computed_hash == token_hash

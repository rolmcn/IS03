import hmac
import hashlib
from eigva_app.config import settings

def generate_login_index(login_id: str) -> str:
    key = settings.SECRET_KEY.encode()
    msg = login_id.encode()
    h = hmac.new(key, msg, hashlib.sha256)
    return h.hexdigest()
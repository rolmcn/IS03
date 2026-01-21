import secrets
import string

DIGITS = string.digits  # 0-9

def generate_login_id(length: int = 6) -> str:
    """
    Sugeneruoja 6 skaitmenų login_id (pvz. 482913)
    """
    return "".join(secrets.choice(DIGITS) for _ in range(length))

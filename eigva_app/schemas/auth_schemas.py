import re
from pydantic import BaseModel, Field, field_validator

# ==================================================
# REGEX
# ==================================================

# Vienas ar keli vardai, atskirti tarpu (be brūkšnelių)
FIRST_NAME_REGEX = (
    r"^[A-Za-zĄČĘĖĮŠŲŪŽąčęėįšųūž]+"
    r"(?: [A-Za-zĄČĘĖĮŠŲŪŽąčęėįšųūž]+)*$"
)

# Viena pavardė arba dviguba su vienu brūkšneliu
LAST_NAME_REGEX = (
    r"^[A-Za-zĄČĘĖĮŠŲŪŽąčęėįšųūž]+"
    r"(?:-[A-Za-zĄČĘĖĮŠŲŪŽąčęėįšųūž]+)?$"
)

# Slaptažodis: 8–20 simbolių, viena didžioji raidė,
# vienas skaičius, vienas specialus simbolis
PASSWORD_REGEX = (
    r"^(?=.*[A-Z])"
    r"(?=.*\d)"
    r"(?=.*[!@#$%^&*()_+\-=])"
    r".{8,20}$"
)

# Login ID: tiksliai 6 skaitmenys
LOGIN_ID_REGEX = r"^\d{6}$"


# ==================================================
# BAZINĖS SCHEMOS
# ==================================================

class EmailBase(BaseModel):
    email: str = Field(...)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Neteisingai nurodytas el. pašto adresas")
        return v


class PasswordBase(BaseModel):
    password: str = Field(...)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.match(PASSWORD_REGEX, v):
            raise ValueError(
                "Slaptažodis turi būti 8–20 simbolių; "
                "turėti bent vieną didžiąją raidę, "
                "bent vieną skaičių ir "
                "bent vieną specialų simbolį (!@#$%^&*()_+-=)"
            )
        return v


# ==================================================
# LOGIN
# ==================================================

class LoginData(BaseModel):
    login_id: str = Field(...)
    password: str = Field(...)

    @field_validator("login_id")
    @classmethod
    def validate_login_id(cls, v: str) -> str:
        v = v.strip()
        if not re.match(LOGIN_ID_REGEX, v):
            raise ValueError("Prisijungimo ID turi būti sudarytas iš 6 skaitmenų")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.match(PASSWORD_REGEX, v):
            raise ValueError("Neteisingas slaptažodžio formatas")
        return v


# ==================================================
# REGISTRACIJA
# ==================================================

class RegistrationData(EmailBase, PasswordBase):
    first_name: str = Field(...)
    last_name: str = Field(...)

    @field_validator("first_name")
    @classmethod
    def validate_first_name(cls, v: str) -> str:
        v = v.strip()
        if not re.match(FIRST_NAME_REGEX, v):
            raise ValueError(
                "Vardas gali būti sudarytas iš raidžių; "
                "vieno ar kelių vardų, atskirtų tarpu"
            )
        return v

    @field_validator("last_name")
    @classmethod
    def validate_last_name(cls, v: str) -> str:
        v = v.strip()
        if not re.match(LAST_NAME_REGEX, v):
            raise ValueError(
                "Pavardė gali būti viena arba dviguba; "
                "dviguba pavardė jungiama vienu brūkšneliu"
            )
        return v


# ==================================================
# FORGOT LOGIN
# ==================================================

class ForgotLoginData(EmailBase, PasswordBase):
    """
    Naudojama prisijungimo duomenų (slaptažodžio / ID) keitimui
    """
    pass
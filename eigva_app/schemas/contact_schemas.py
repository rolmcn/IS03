from pydantic import BaseModel, field_validator
import re

class ContactData(BaseModel):
    email: str | None = None
    phone: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if not v:
            return None
        pattern = r"[^@]+@[^@]+\.[^@]+"
        if not re.match(pattern, v):
            raise ValueError("Neteisingai nurodytas el. pašto adresas")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if not v:
            return None
        if not v.isdigit() or len(v) != 8:
            raise ValueError("Neteisingai nurodytas telefono numeris (turi būti 8 skaitmenys)")
        return v

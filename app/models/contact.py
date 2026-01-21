from pydantic import BaseModel, field_validator, model_validator
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

    @model_validator(mode="after")
    def check_exactly_one_contact(self):
        if (self.email and self.phone) or (not self.email and not self.phone):
            raise ValueError(
                "Prašome nurodyti vieną kontakto variantą (el. pašto adresą arba telefono numerį)"
            )
        return self

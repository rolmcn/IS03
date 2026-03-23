import re
from pydantic import BaseModel, Field, field_validator, model_validator

# ==================================================
# REGEX
# ==================================================
HOUSE_APT_REGEX = r"^[0-9A-Za-z\s\-\/]+$"
SETTLEMENT_REGEX = re.compile(r"^[a-zA-ZąčęėįšųūžĄČĘĖĮŠŲŪŽ \-]+$")
EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")

# ==================================================
# BAZINĖS SCHEMOS
# ==================================================

class EmailBase(BaseModel):
    email: str = Field(...)

    @field_validator("email")
    @classmethod
    def validate_email_lt(cls, v: str) -> str:
        v = v.strip()
        if not EMAIL_REGEX.match(v):
            raise ValueError("Neteisingai nurodytas el. pašto adresas")
        return v.lower()


class FullNameBase(BaseModel):
    full_name: str = Field(...)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        v = v.strip()
        if len(v.split()) < 2:
            raise ValueError(
                "Pavadinimą turi sudaryti bent du žodžiai, kurių vienas teisinės formos santrumpa (UAB, AB, MB, IĮ, ŪB, TŪB, KŪB, VšĮ ir t.t.)"
            )
        return v


class IdentificationCodeBase(BaseModel):
    identification_code: str | None = Field(default=None)

    @field_validator("identification_code")
    @classmethod
    def validate_identification_code(cls, v: str | None):
        if not v:
            return v
        if not v.isdigit() or len(v) != 9:
            raise ValueError("Įmonės kodas turi būti iš 9 skaičių")
        return v


class VatCodeBase(BaseModel):
    vat_code: str | None = Field(default=None)

    @field_validator("vat_code")
    @classmethod
    def validate_vat_code(cls, v: str | None):
        if not v:
            return v
        if not v.isdigit() or len(v) != 12:
            raise ValueError("PVM kodas turi būti iš 12 skaičių")
        return v


class PhoneBase(BaseModel):
    mobile_phone: str | None = Field(default=None)

    @field_validator("mobile_phone")
    @classmethod
    def validate_phone(cls, v: str | None):
        if not v:
            return v
        if not v.isdigit() or len(v) != 8:
            raise ValueError("Telefono numeris turi būti iš 8 skaičių")
        return v


class StreetBase(BaseModel):
    street: str = Field(...)

    @field_validator("street")
    @classmethod
    def validate_street(cls, v: str) -> str:
        v = v.strip()
        if len(v.split()) < 2:
            raise ValueError(
                "Gatvės pavadinimą turi sudaryti bent du žodžiai, kurių vienas gatvės tipo trumpinys (g., a., al., sk., pr., pl., kel. ir t.t.)"
            )
        return v


class HouseNumberBase(BaseModel):
    house_number: str = Field(...)

    @field_validator("house_number")
    @classmethod
    def validate_house_number(cls, v: str) -> str:
        if not re.match(HOUSE_APT_REGEX, v):
            raise ValueError(
                "Neteisingai nurodytas namo numeris. Leidžiama įvesti iki 9 simbolių (raides, skaičius, '-' ir '/')."
            )
        return v.strip()


class ApartmentNumberBase(BaseModel):
    apartment_number: str | None = Field(default=None)

    @field_validator("apartment_number")
    @classmethod
    def validate_apartment(cls, v: str | None):
        if not v:
            return v
        if not re.match(HOUSE_APT_REGEX, v):
            raise ValueError(
                "Neteisingai nurodytas buto numeris. Leidžiama įvesti iki 3 simbolių (raides, skaičius, '-' ir '/')."
            )
        return v.strip()


class PostalCodeBase(BaseModel):
    postal_code: str = Field(...)

    @field_validator("postal_code")
    @classmethod
    def validate_postal_code(cls, v: str):
        if not v.isdigit() or len(v) != 5:
            raise ValueError("Pašto kodas turi būti iš 5 skaičių")
        return v


class SettlementBase(BaseModel):
    settlement: str = Field(..., min_length=3)

    @field_validator("settlement")
    @classmethod
    def validate_settlement(cls, v: str):
        v = v.strip()
        if not SETTLEMENT_REGEX.match(v):
            raise ValueError(
                "Gyvenvietės pavadinime leidžiamos tik raidės ir '-'"
            )
        return v


# ==================================================
# PILNA PAYER SCHEMA
# ==================================================

class PayerSchema(
    FullNameBase,
    IdentificationCodeBase,
    VatCodeBase,
    PhoneBase,
    EmailBase,
    StreetBase,
    HouseNumberBase,
    ApartmentNumberBase,
    PostalCodeBase,
    SettlementBase
):
    payer_type: str = Field(...)
    vat_status: str = Field(...)
    municipality: str = Field(...)
    country: str | None = Field(default=None)

    @model_validator(mode="after")
    def adjust_fields_for_logic(self):

        # jei fizinis asmuo, įmonės kodas ignoruojamas
        if self.payer_type == "physical":
            self.identification_code = None

        # jei ne PVM mokėtojas, PVM kodas ignoruojamas
        if self.vat_status != "yes":
            self.vat_code = None

        return self
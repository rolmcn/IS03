from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Literal
from decimal import Decimal, ROUND_HALF_UP


class OrderForm(BaseModel):
    licenses_quantity: int = Field(ge=0, le=100)
    licenses_duration: int = Field(ge=0, le=12)

    financial_operation_type: Literal["add", "credit", "return"] | None = None

    refund_bank_account: str | None = None

    financial_amount: Decimal | None = None

    terms_agree: bool

    # -------------------------
    # NORMALIZACIJA:
    # -------------------------
    @field_validator("financial_amount", mode="before")
    def normalize_amount(v):
        if v is None or v == "":
            return None

        if isinstance(v, str):
            v = v.replace(",", ".").strip()

        return v

    @field_validator("refund_bank_account", mode="before")
    @classmethod
    def normalize_iban_input(cls, v):
        if v == "" or v is None:
            return None
        return v

    # -------------------------
    # IBAN VALIDACIJA
    # -------------------------
    @field_validator("refund_bank_account")
    @classmethod
    def validate_iban(cls, v):
        if v is None:
            return None

        v = v.strip().replace(" ", "")

        if not (v.isdigit() and len(v) == 18):
            raise ValueError(
                'Banko sąskaita turi būti sudaryta be prefikso "LT" iš 18 skaičių'
            )

        return v

    # -------------------------
    # SUMA VALIDACIJA
    # -------------------------
    @field_validator("financial_amount")
    @classmethod
    def validate_amount(cls, v):
        if v is None:
            return v

        v = v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return v

    # -------------------------
    # MINIMALŪS LAUKŲ RYŠIAI
    # -------------------------
    @model_validator(mode="after")
    def validate_basic_logic(self):
        # jei yra operacijos tipas → turi būti suma
        if self.financial_operation_type and self.financial_amount is None:
            raise ValueError("Įveskite sumą")

        # jei yra suma → turi būti operacijos tipas
        if self.financial_amount is not None and not self.financial_operation_type:
            raise ValueError("Pasirinkite operacijos tipą")

        # return → būtina sąskaita
        if self.financial_operation_type == "return":
            if not self.refund_bank_account:
                raise ValueError("Įveskite banko sąskaitos numerį")

        return self
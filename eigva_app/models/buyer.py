from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from eigva_app.database import Base
from eigva_app.core.security.crypto import decrypt_data, encrypt_data
import hashlib


class Buyer(Base):
    __tablename__ = "buyers"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    status = Column(String(8), nullable=False, default="pending")  # pending, active, inactive
    buyer_type = Column(String(8), nullable=True)  # physical, legal
    vat_status = Column(String(3), nullable=True)  # yes, no
    full_name_encrypted = Column(String(255), nullable=True)
    identification_code_encrypted = Column(String(255), nullable=True)
    identification_code_hash = Column(String(64), nullable=True, unique=True)
    vat_code_encrypted = Column(String(255), nullable=True)
    vat_code_hash = Column(String(64), nullable=True, unique=True)
    street_encrypted = Column(String(255), nullable=True)
    house_number_encrypted = Column(String(255), nullable=True)
    apartment_number_encrypted = Column(String(255), nullable=True)
    postal_code_encrypted = Column(String(255), nullable=True)
    settlement_encrypted = Column(String(255), nullable=True)
    municipality_encrypted = Column(String(255), nullable=True)
    country_encrypted = Column(String(255), nullable=True)
    mobile_phone_encrypted = Column(String(255), nullable=True)
    email_encrypted = Column(String(255), nullable=True)
    full_name_email_hash = Column(String(64), nullable=True, unique=True)

    users = relationship("User", back_populates="buyer", lazy="selectin")
    invoices = relationship("Invoice", back_populates="buyer", lazy="selectin")

    # Encrypted field getters/setters
    @property
    def full_name(self) -> str | None:
        return decrypt_data(self.full_name_encrypted) if self.full_name_encrypted else None

    @full_name.setter
    def full_name(self, value: str):
        self.full_name_encrypted = encrypt_data(value)

    @property
    def identification_code(self) -> str | None:
        return decrypt_data(self.identification_code_encrypted) if self.identification_code_encrypted else None

    @identification_code.setter
    def identification_code(self, value: str):
        self.identification_code_encrypted = encrypt_data(value)

    @property
    def vat_code(self) -> str | None:
        return decrypt_data(self.vat_code_encrypted) if self.vat_code_encrypted else None

    @vat_code.setter
    def vat_code(self, value: str):
        self.vat_code_encrypted = encrypt_data(value)

    @property
    def street(self) -> str | None:
        return decrypt_data(self.street_encrypted) if self.street_encrypted else None

    @street.setter
    def street(self, value: str):
        self.street_encrypted = encrypt_data(value)

    @property
    def house_number(self) -> str | None:
        return decrypt_data(self.house_number_encrypted) if self.house_number_encrypted else None

    @house_number.setter
    def house_number(self, value: str):
        self.house_number_encrypted = encrypt_data(value)

    @property
    def apartment_number(self) -> str | None:
        return decrypt_data(self.apartment_number_encrypted) if self.apartment_number_encrypted else None

    @apartment_number.setter
    def apartment_number(self, value: str):
        self.apartment_number_encrypted = encrypt_data(value)

    @property
    def postal_code(self) -> str | None:
        return decrypt_data(self.postal_code_encrypted) if self.postal_code_encrypted else None

    @postal_code.setter
    def postal_code(self, value: str):
        self.postal_code_encrypted = encrypt_data(value)

    @property
    def settlement(self) -> str | None:
        return decrypt_data(self.settlement_encrypted) if self.settlement_encrypted else None

    @settlement.setter
    def settlement(self, value: str):
        self.settlement_encrypted = encrypt_data(value)

    @property
    def municipality(self) -> str | None:
        return decrypt_data(self.municipality_encrypted) if self.municipality_encrypted else None

    @municipality.setter
    def municipality(self, value: str):
        self.municipality_encrypted = encrypt_data(value)

    @property
    def country(self) -> str | None:
        return decrypt_data(self.country_encrypted) if self.country_encrypted else None

    @country.setter
    def country(self, value: str):
        self.country_encrypted = encrypt_data(value)

    @property
    def mobile_phone(self) -> str | None:
        return decrypt_data(self.mobile_phone_encrypted) if self.mobile_phone_encrypted else None

    @mobile_phone.setter
    def mobile_phone(self, value: str):
        self.mobile_phone_encrypted = encrypt_data(value)

    @property
    def email(self) -> str | None:
        return decrypt_data(self.email_encrypted) if self.email_encrypted else None

    @email.setter
    def email(self, value: str):
        self.email_encrypted = encrypt_data(value)

    # Hash field
    @staticmethod
    def hash_vat_code(vat_code: str) -> str:
        return hashlib.sha256(vat_code.encode("utf-8")).hexdigest()

    @staticmethod
    def hash_identification_code(ident_code: str) -> str:
        return hashlib.sha256(ident_code.encode("utf-8")).hexdigest()

    @staticmethod
    def hash_full_name_email(full_name: str, email: str) -> str:
        combined = f"{full_name.strip().lower()}|{email.strip().lower()}"
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()
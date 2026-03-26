from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from eigva_app.database import Base
from eigva_app.core.security.crypto import encrypt_data, decrypt_data
from decimal import Decimal, ROUND_HALF_UP

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="issued")  # issued, cancelled
    settled_at = Column(DateTime(timezone=True), nullable=True)
    series = Column(String(2), nullable=False)  # EI, EP, EC
    number = Column(Integer, nullable=False)
    full_number = Column(String(12), nullable=False, unique=True)  # EI2603250001
    date = Column(DateTime(timezone=True), nullable=False)

    _total_without_vat_eur = Column("total_without_vat_eur", Numeric(12, 2), nullable=False)
    _vat_rate_pct = Column("vat_rate_pct", Numeric(5, 2), nullable=False)
    _vat_amount_eur = Column("vat_amount_eur", Numeric(12, 2), nullable=False)
    _total_with_vat_eur = Column("total_with_vat_eur", Numeric(12, 2), nullable=False)

    total_with_vat_eur_in_words = Column(String(255), nullable=False)

    buyer_full_name_encrypted = Column(String(255), nullable=False)
    buyer_identification_code_encrypted = Column(String(255), nullable=True)
    buyer_vat_code_encrypted = Column(String(255), nullable=True)
    buyer_street_encrypted = Column(String(255), nullable=False)
    buyer_house_number_encrypted = Column(String(255), nullable=False)
    buyer_apartment_number_encrypted = Column(String(255), nullable=True)
    buyer_postal_code_encrypted = Column(String(255), nullable=False)
    buyer_settlement_encrypted = Column(String(255), nullable=False)
    buyer_municipality_encrypted = Column(String(255), nullable=False)
    buyer_country_encrypted = Column(String(255), nullable=False)
    buyer_mobile_phone_encrypted = Column(String(255), nullable=True)
    buyer_email_encrypted = Column(String(255), nullable=False)

    seller_full_name = Column(String(255), nullable=False)
    seller_identification_code = Column(String(255), nullable=False)
    seller_vat_code = Column(String(255), nullable=False)
    seller_address = Column(String(255), nullable=False)
    seller_phone = Column(String(20), nullable=False)
    seller_email = Column(String(255), nullable=False)
    seller_bank_name = Column(String(50), nullable=False)
    seller_current_account = Column(String(50), nullable=False)

    buyer_id = Column(Integer, ForeignKey("buyers.id"), nullable=False)

    buyer = relationship("Buyer", back_populates="invoices", lazy="selectin")
    items = relationship("InvoiceItem", back_populates="invoice", lazy="selectin")

    # Decimal rounding helper
    @staticmethod
    def round_currency(value):
        if value is None:
            return None
        return Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    # Properties with rounding
    @property
    def total_without_vat_eur(self):
        return self._total_without_vat_eur

    @total_without_vat_eur.setter
    def total_without_vat_eur(self, value):
        self._total_without_vat_eur = self.round_currency(value)

    @property
    def vat_rate_pct(self):
        return self._vat_rate_pct

    @vat_rate_pct.setter
    def vat_rate_pct(self, value):
        self._vat_rate_pct = self.round_currency(value)

    @property
    def vat_amount_eur(self):
        return self._vat_amount_eur

    @vat_amount_eur.setter
    def vat_amount_eur(self, value):
        self._vat_amount_eur = self.round_currency(value)

    @property
    def total_with_vat_eur(self):
        return self._total_with_vat_eur

    @total_with_vat_eur.setter
    def total_with_vat_eur(self, value):
        self._total_with_vat_eur = self.round_currency(value)

    # Encrypted field getters/setters
    @property
    def buyer_full_name(self):
        return decrypt_data(self.buyer_full_name_encrypted) if self.buyer_full_name_encrypted else None

    @buyer_full_name.setter
    def buyer_full_name(self, value: str):
        self.buyer_full_name_encrypted = encrypt_data(value)

    @property
    def buyer_identification_code(self):
        return decrypt_data(self.buyer_identification_code_encrypted) if self.buyer_identification_code_encrypted else None

    @buyer_identification_code.setter
    def buyer_identification_code(self, value: str):
        self.buyer_identification_code_encrypted = encrypt_data(value)

    @property
    def buyer_vat_code(self):
        return decrypt_data(self.buyer_vat_code_encrypted) if self.buyer_vat_code_encrypted else None

    @buyer_vat_code.setter
    def buyer_vat_code(self, value: str):
        self.buyer_vat_code_encrypted = encrypt_data(value)

    @property
    def buyer_email(self):
        return decrypt_data(self.buyer_email_encrypted) if self.buyer_email_encrypted else None

    @buyer_email.setter
    def buyer_email(self, value: str):
        self.buyer_email_encrypted = encrypt_data(value)
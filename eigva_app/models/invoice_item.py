from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from eigva_app.database import Base

class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    service_type = Column(String(10), nullable=False)  # LIC, SMS
    service_description = Column(String(255), nullable=False)
    service_note = Column(String(255), nullable=True)
    duration = Column(Integer, nullable=False)  # months
    date_from = Column(DateTime(timezone=True), nullable=False)
    date_until = Column(DateTime(timezone=True), nullable=False)
    unit = Column(String(10), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price_eur = Column(Numeric(12,2), nullable=False)
    amount_eur = Column(Numeric(12,2), nullable=False)
    operation_type = Column(String(20), nullable=True)
    refund_bank_account = Column(String(50), nullable=True)

    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    invoice = relationship("Invoice", back_populates="items", lazy="selectin")
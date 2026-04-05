from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from eigva_app.database import Base


class SmsTransaction(Base):
    __tablename__ = "sms_transactions"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    buyer_id = Column(Integer, ForeignKey("buyers.id"), nullable=False)
    type = Column(String(10), nullable=False)     # 'credit' | 'debit'
    reason = Column(String(30), nullable=False)   # 'topup' | 'sms_send' | 'license_purchase' | 'refund'
    amount_eur = Column(Numeric(12, 2), nullable=False)
    sms_count = Column(Integer, nullable=True)  # naudojamas tik sms_send
    related_invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    invoiced = Column(Boolean, nullable=False, default=False)     # False - dar neįtraukta į PVM sąskaitą; True - jau įtraukta
    price_per_sms = Column(Numeric(12, 6), nullable=True)

    buyer = relationship("Buyer", back_populates="sms_transactions", lazy="selectin")
    invoice = relationship("Invoice", back_populates="sms_transactions", lazy="selectin")
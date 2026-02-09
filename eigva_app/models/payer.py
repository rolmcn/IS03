from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from eigva_app.database import Base
from eigva_app.models.user_payer_association import user_payer_association

class Payer(Base):
    __tablename__ = "payers"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    status = Column(String(8), nullable=True)  # pending, active, inactive
    payer_type = Column(String(8), nullable=True)  # physical, legal

    full_name_encrypted = Column(String(255), nullable=True)
    identification_code_encrypted = Column(String(255), nullable=True, unique=True)
    vat_code_encrypted = Column(String(255), nullable=True, unique=True)

    street_encrypted = Column(String(255), nullable=True)
    house_number_encrypted = Column(String(255), nullable=True)
    apartment_number_encrypted = Column(String(255), nullable=True)
    postal_code_encrypted = Column(String(255), nullable=True)
    settlement_encrypted = Column(String(255), nullable=True)
    municipality_encrypted = Column(String(255), nullable=True)
    country_encrypted = Column(String(255), nullable=True)

    mobile_phone_encrypted = Column(String(255), nullable=True)
    email_encrypted = Column(String(255), nullable=True)

    users = relationship(
        "User",
        secondary=user_payer_association,
        back_populates="payers"
    )


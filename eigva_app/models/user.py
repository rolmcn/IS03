from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from eigva_app.database import Base
from eigva_app.core.security.crypto import decrypt_data

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    status = Column(String(8), nullable=False, default="pending")  # active, pending, inactive
    super_user = Column(Boolean, nullable=False, default=False)
    first_name_encrypted = Column(String(255), nullable=False)
    last_name_encrypted = Column(String(255), nullable=False)
    email_encrypted = Column(String(255), nullable=False)
    email_index = Column(String(64), unique=True, index=True, nullable=False)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    mobile_phone_encrypted = Column(String(255), nullable=True, default=None)
    mobile_phone_index = Column(String(64), unique=True, index=True, nullable=True, default=None)
    login_index = Column(String(64), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    reset_password_hash = Column(String(255), nullable=True)
    confirmation_token_hash = Column(String(64), nullable=True)
    reset_confirmation_token_hash = Column(String(64), nullable=True)
    confirmation_token_expires = Column(DateTime(timezone=True), nullable=True)
    reset_confirmation_token_expires = Column(DateTime(timezone=True), nullable=True)

    buyer_id = Column(Integer, ForeignKey("buyers.id"), nullable=True, index=True)

    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    buyer = relationship("Buyer", back_populates="users", lazy="selectin")

    # Encrypted field getters/setters
    @property
    def first_name(self) -> str:
        return decrypt_data(self.first_name_encrypted)

    @property
    def last_name(self) -> str:
        return decrypt_data(self.last_name_encrypted)

    @property
    def email(self) -> str:
        return decrypt_data(self.email_encrypted)

    @property
    def mobile_phone(self) -> str | None:
        if self.mobile_phone_encrypted:
            return decrypt_data(self.mobile_phone_encrypted)
        return None

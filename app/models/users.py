from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base

class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    status = Column(String(8), nullable=False, default="pending")  # active, pending, inactive
    super_user = Column(Boolean, nullable=False, default=False)

    first_name_encrypted = Column(String(255), nullable=False)
    last_name_encrypted = Column(String(255), nullable=False)
    email_encrypted = Column(String(255), nullable=False)
    mobile_phone_encrypted = Column(String(255), nullable=True, default=None)

    email_index = Column(String(64), unique=True, index=True, nullable=False)
    mobile_phone_index = Column(String(64), unique=True, index=True, nullable=True, default=None)
    login_index = Column(String(64), unique=True, index=True, nullable=True)

    password_hash = Column(String(255), nullable=False)
    confirmation_token_hash = Column(String(64), nullable=True)

    confirmation_token_expires = Column(DateTime, nullable=True)


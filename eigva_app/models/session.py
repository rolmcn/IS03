from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import relationship
from eigva_app.database import Base

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship(
        "User",
        back_populates="sessions"
    )

    @staticmethod
    def expiry():
        return datetime.now(timezone.utc) + timedelta(hours=12)

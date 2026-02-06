from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from enum import Enum as PyEnum

from app.database import Base


class MessageEventType(str, PyEnum): # <-- papildžius įtraukti į db
    REGISTRATION = "registration"
    POST_REGISTRATION = "post_registration"
    FIRST_LOGIN = "first_login"
    USER_DATA_CHANGE = "user_data_change"
    BUYER_DATA_CHANGE = "buyer_data_change"


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    msg_title = Column(String(255), nullable=True)
    msg_content = Column(String, nullable=False)

    msg_type = Column(String(50), nullable=False)   # sms, email, system
    msg_status = Column(String(50), default="sent") # sent, failed, read
    msg_read = Column(DateTime(timezone=True), nullable=True, default=None)

    msg_created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    msg_event_type = Column(String(50), nullable=False)

    user = relationship("User", back_populates="messages")

    def __repr__(self):
        return (
            f"<Message {self.id} user={self.user_id} "
            f"type={self.msg_type} status={self.msg_status} "
            f"read={self.msg_read} event={self.msg_event_type}>"
        )
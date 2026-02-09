from sqlalchemy import Table, Column, Integer, ForeignKey
from eigva_app.database import Base

user_payer_association = Table(
    "user_payer_association",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("payer_id", Integer, ForeignKey("payers.id"), primary_key=True)
)

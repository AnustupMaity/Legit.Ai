from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class Tenant(Base):
    __tablename__ = 'tenants'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    domain: Mapped[str | None] = mapped_column(String(256), nullable=True)

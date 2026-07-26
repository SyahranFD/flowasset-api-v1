import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.types import Uuid

from app.core.database import Base
from app.core.security import wib_now


class User(Base):
    __tablename__ = "users"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    npwp = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, default=wib_now)

from sqlalchemy import Column, Integer, String, TIMESTAMP, BIGINT
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class TempMailUsers(Base):
    __tablename__ = "temp_mail_users"
    id = Column(BIGINT, primary_key=True)
    email = Column(String, nullable=True)
    name = Column(String, nullable=False)
    username = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, nullable=False, onupdate=datetime.utcnow)

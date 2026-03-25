# SmartStore ERP — User Model (Login/Auth ke liye)
# Ye table login credentials store karega — Phase 2 mein JWT auth ke saath use hoga

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)         # Bcrypt hashed — plain text NEVER store
    full_name = Column(String(200), nullable=True)
    role = Column(String(20), default="staff")                    # owner / cashier / staff
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

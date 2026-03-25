# SmartStore ERP — Dealer Model
# Ye table saare dealers/suppliers store karega (Udhaar/Khata system ke liye)

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.sql import func

from app.core.database import Base


class Dealer(Base):
    __tablename__ = "dealers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)       # Dealer ka naam
    phone = Column(String(15), nullable=True, index=True)        # Phone number
    email = Column(String(100), nullable=True)
    address = Column(String(500), nullable=True)                 # Address
    gstin = Column(String(15), nullable=True)                    # GSTIN number (if registered)
    credit_limit = Column(Float, default=0.0)                    # Max udhaar allowed
    outstanding = Column(Float, default=0.0)                     # Current udhaar baaki
    dealer_type = Column(String(50), default="supplier")         # supplier / customer / both
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

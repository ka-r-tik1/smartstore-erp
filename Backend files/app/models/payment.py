# SmartStore ERP — Payment Model
# Udhaar payment collection log — kab kitna vasool kiya

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func

from app.core.database import Base


class Payment(Base):
    """Jab dealer udhaar ka paisa deta hai — wo log yahan hota hai"""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    dealer_id = Column(Integer, ForeignKey("dealers.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)                    # Kitna collect kiya
    payment_mode = Column(String(30), default="cash")         # cash / upi / card
    reference = Column(String(100), nullable=True)            # Receipt number
    notes = Column(Text, nullable=True)
    outstanding_before = Column(Float, nullable=False)        # Pehle kitna baaki tha
    outstanding_after = Column(Float, nullable=False)         # Ab kitna baaki hai
    collected_by = Column(String(100), nullable=True)         # Kisne vasool kiya
    created_at = Column(DateTime, server_default=func.now(), index=True)

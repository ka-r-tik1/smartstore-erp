# SmartStore ERP — GST Model
# GST config, HSN codes, aur e-Invoice records store karta hai

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func

from app.core.database import Base


class GSTConfig(Base):
    """Store ka GST configuration — GSTIN, state, registration details"""
    __tablename__ = "gst_config"

    id = Column(Integer, primary_key=True, index=True)
    business_name = Column(String(200), nullable=False)          # Dukaan ka naam
    gstin = Column(String(15), nullable=True, unique=True)       # 15-digit GSTIN
    state_name = Column(String(100), nullable=False, default="Maharashtra")
    state_code = Column(String(5), nullable=False, default="27") # Maharashtra = 27
    is_gst_registered = Column(Boolean, default=False)           # Registered hai?
    composition_scheme = Column(Boolean, default=False)          # Composition dealer?
    annual_turnover = Column(Float, default=0.0)                 # Annual turnover estimate
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class HSNCode(Base):
    """HSN Code table — product ke liye GST rate lookup"""
    __tablename__ = "hsn_codes"

    id = Column(Integer, primary_key=True, index=True)
    hsn_code = Column(String(20), nullable=False, unique=True, index=True)
    description = Column(String(300), nullable=False)
    gst_rate = Column(Float, nullable=False, default=0.0)        # 0, 5, 12, 18, 28
    cess_rate = Column(Float, default=0.0)                       # Extra cess (like tobacco, aerated drinks)
    category = Column(String(100), nullable=True)                # Food, Textile, etc.
    created_at = Column(DateTime, server_default=func.now())


class EInvoice(Base):
    """e-Invoice / IRN records — each GST invoice ka record"""
    __tablename__ = "einvoices"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    invoice_number = Column(String(50), nullable=False)
    irn = Column(String(64), nullable=True)                      # Invoice Reference Number (64 char hash)
    ack_number = Column(String(20), nullable=True)               # Acknowledgement number
    ack_date = Column(DateTime, nullable=True)                   # Acknowledgement date
    qr_data = Column(Text, nullable=True)                        # QR code content
    buyer_gstin = Column(String(15), nullable=True)              # Buyer's GSTIN (B2B ke liye)
    supply_type = Column(String(10), default="B2C")              # B2B / B2C / EXPORT
    status = Column(String(20), default="pending")               # pending / generated / cancelled
    cancel_reason = Column(String(200), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

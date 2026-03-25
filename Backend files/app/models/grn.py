# SmartStore ERP — GRN (Goods Received Note) Model
# Jab supplier se maal aata hai, GRN banate hain
# PO ke against kitna maal actually aaya — quality check + stock update

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Date, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class GRN(Base):
    """Goods Received Note — supplier se maal aane ka record"""
    __tablename__ = "grns"

    id = Column(Integer, primary_key=True, index=True)
    grn_number = Column(String(50), unique=True, nullable=False, index=True)  # GRN-2026-0001
    po_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=True)  # Kaunse PO ke against
    po_number = Column(String(50), nullable=True)
    supplier_id = Column(Integer, ForeignKey("dealers.id"), nullable=False)
    received_date = Column(Date, nullable=False)
    invoice_number = Column(String(100), nullable=True)           # Supplier ka invoice number
    invoice_date = Column(Date, nullable=True)
    vehicle_number = Column(String(50), nullable=True)            # Delivery vehicle
    status = Column(String(20), default="draft", index=True)      # draft / verified / stock_updated
    quality_check = Column(Boolean, default=False)                # Quality check done?
    quality_notes = Column(Text, nullable=True)
    subtotal = Column(Float, default=0.0)
    gst_amount = Column(Float, default=0.0)
    grand_total = Column(Float, default=0.0)
    received_by = Column(String(100), nullable=True)
    verified_by = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    items = relationship("GRNItem", back_populates="grn")


class GRNItem(Base):
    """GRN mein konse products kitne aaye"""
    __tablename__ = "grn_items"

    id = Column(Integer, primary_key=True, index=True)
    grn_id = Column(Integer, ForeignKey("grns.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(200), nullable=False)
    qty_ordered = Column(Integer, default=0)                      # PO mein kitna tha
    qty_received = Column(Integer, nullable=False)                # Actually kitna aaya
    qty_accepted = Column(Integer, nullable=False)                # Quality pass kitna
    qty_rejected = Column(Integer, default=0)                     # Reject hua kitna
    unit_price = Column(Float, nullable=False)
    gst_rate = Column(Float, default=0.0)
    gst_amount = Column(Float, default=0.0)
    total = Column(Float, nullable=False)
    batch_number = Column(String(100), nullable=True)
    expiry_date = Column(Date, nullable=True)
    rejection_reason = Column(String(200), nullable=True)

    grn = relationship("GRN", back_populates="items")

# SmartStore ERP — Purchase Order Models
# Supplier se maal mangwane ka system — PO banao, approve karo, maal receive karo

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class PurchaseOrder(Base):
    """Purchase Order — supplier ko samaan ka order"""
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String(50), unique=True, nullable=False, index=True)  # PO-2026-0001
    supplier_id = Column(Integer, ForeignKey("dealers.id"), nullable=False, index=True)
    status = Column(String(20), default="draft", index=True)
    # status: draft / approved / received / cancelled
    subtotal = Column(Float, default=0.0)
    gst_amount = Column(Float, default=0.0)
    grand_total = Column(Float, default=0.0)
    expected_date = Column(Date, nullable=True)              # Kab tak aana chahiye
    received_date = Column(Date, nullable=True)              # Kab mila
    notes = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=True)
    approved_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    items = relationship("PurchaseOrderItem", back_populates="purchase_order")


class PurchaseOrderItem(Base):
    """PO mein konse products kitne chahiye"""
    __tablename__ = "purchase_order_items"

    id = Column(Integer, primary_key=True, index=True)
    po_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(200), nullable=False)
    qty_ordered = Column(Integer, nullable=False)            # Kitna mangwaya
    qty_received = Column(Integer, default=0)                # Kitna mila
    unit_price = Column(Float, nullable=False)               # Purchase price per unit
    gst_rate = Column(Float, default=0.0)
    gst_amount = Column(Float, default=0.0)
    total = Column(Float, nullable=False)

    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="items")

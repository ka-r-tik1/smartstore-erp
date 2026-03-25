# SmartStore ERP — Returns Models
# Sales Return: Customer product wapas karta hai
# Purchase Return: Supplier ko goods wapas bhejte hain

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class SalesReturn(Base):
    """Sales Return — customer ne product wapas kiya"""
    __tablename__ = "sales_returns"

    id = Column(Integer, primary_key=True, index=True)
    return_number = Column(String(50), unique=True, nullable=False, index=True)  # SR-2026-0001
    original_invoice = Column(String(50), nullable=True)          # Kaunsa bill tha
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    dealer_id = Column(Integer, ForeignKey("dealers.id"), nullable=True)  # Kaun customer
    return_date = Column(Date, nullable=False)
    reason = Column(String(200), nullable=True)                   # Kyun wapas kiya
    status = Column(String(20), default="pending", index=True)    # pending / approved / refunded
    refund_mode = Column(String(30), nullable=True)               # cash / credit_note / upi
    subtotal = Column(Float, default=0.0)
    gst_amount = Column(Float, default=0.0)
    total_refund = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    processed_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    items = relationship("SalesReturnItem", back_populates="sales_return")


class SalesReturnItem(Base):
    """Sales Return mein konse products kitne wapas aaye"""
    __tablename__ = "sales_return_items"

    id = Column(Integer, primary_key=True, index=True)
    return_id = Column(Integer, ForeignKey("sales_returns.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(200), nullable=False)
    qty_returned = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    gst_rate = Column(Float, default=0.0)
    gst_amount = Column(Float, default=0.0)
    total = Column(Float, nullable=False)
    condition = Column(String(50), default="good")   # good / damaged / expired

    sales_return = relationship("SalesReturn", back_populates="items")


class PurchaseReturn(Base):
    """Purchase Return — supplier ko maal wapas bheja"""
    __tablename__ = "purchase_returns"

    id = Column(Integer, primary_key=True, index=True)
    return_number = Column(String(50), unique=True, nullable=False, index=True)  # PR-2026-0001
    original_po = Column(String(50), nullable=True)               # Kaunsa PO tha
    po_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("dealers.id"), nullable=False)
    return_date = Column(Date, nullable=False)
    reason = Column(String(200), nullable=True)
    status = Column(String(20), default="pending", index=True)    # pending / sent / debit_note
    subtotal = Column(Float, default=0.0)
    gst_amount = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    debit_note_number = Column(String(50), nullable=True)         # Debit note ref
    notes = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    items = relationship("PurchaseReturnItem", back_populates="purchase_return")


class PurchaseReturnItem(Base):
    """Purchase Return mein konse products kitne gaye"""
    __tablename__ = "purchase_return_items"

    id = Column(Integer, primary_key=True, index=True)
    return_id = Column(Integer, ForeignKey("purchase_returns.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(200), nullable=False)
    qty_returned = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    gst_rate = Column(Float, default=0.0)
    gst_amount = Column(Float, default=0.0)
    total = Column(Float, nullable=False)

    purchase_return = relationship("PurchaseReturn", back_populates="items")

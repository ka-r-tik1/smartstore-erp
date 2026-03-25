# SmartStore ERP — Order & Order Items Models
# Ye tables billing/orders store karengi (POS se jo bill banta hai)

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)  # INV-2026-0001
    dealer_id = Column(Integer, ForeignKey("dealers.id"), nullable=True)          # Kis dealer ka order
    order_type = Column(String(20), default="sale")               # sale / purchase / return
    subtotal = Column(Float, default=0.0)                         # Items ka total (before GST)
    gst_amount = Column(Float, default=0.0)                       # Total GST
    discount = Column(Float, default=0.0)                         # Discount amount
    grand_total = Column(Float, default=0.0)                      # Final amount
    payment_mode = Column(String(30), default="cash")             # cash / upi / card / udhaar
    payment_status = Column(String(20), default="paid")           # paid / pending / partial
    notes = Column(Text, nullable=True)                           # Any notes
    created_at = Column(DateTime, server_default=func.now(), index=True)

    # Relationships
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(200), nullable=False)            # Snapshot — product naam save
    qty = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)                    # Per unit price
    gst_rate = Column(Float, default=0.0)                         # GST % on this item
    gst_amount = Column(Float, default=0.0)                       # GST amount for this item
    total = Column(Float, nullable=False)                         # qty × unit_price + GST

    # Relationships
    order = relationship("Order", back_populates="items")

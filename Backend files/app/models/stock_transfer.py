# SmartStore ERP — Stock Transfer Model
# Ek location se doosri location pe stock move karna
# Godown → Shop, Shop A → Shop B

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class StockTransfer(Base):
    """Stock Transfer — ek jagah se doosri jagah stock move"""
    __tablename__ = "stock_transfers"

    id = Column(Integer, primary_key=True, index=True)
    transfer_number = Column(String(50), unique=True, nullable=False, index=True)  # ST-2026-0001
    from_location = Column(String(100), nullable=False)           # Kahan se (Godown / Shop A)
    to_location = Column(String(100), nullable=False)             # Kahan (Shop B / Counter)
    transfer_date = Column(Date, nullable=False)
    status = Column(String(20), default="pending", index=True)    # pending / in_transit / received / cancelled
    total_items = Column(Integer, default=0)
    total_value = Column(Float, default=0.0)
    requested_by = Column(String(100), nullable=True)
    dispatched_by = Column(String(100), nullable=True)
    received_by = Column(String(100), nullable=True)
    received_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    items = relationship("StockTransferItem", back_populates="transfer")


class StockTransferItem(Base):
    """Transfer mein kaunse products kitne bheje"""
    __tablename__ = "stock_transfer_items"

    id = Column(Integer, primary_key=True, index=True)
    transfer_id = Column(Integer, ForeignKey("stock_transfers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(200), nullable=False)
    qty_requested = Column(Integer, nullable=False)
    qty_dispatched = Column(Integer, default=0)
    qty_received = Column(Integer, default=0)
    unit_value = Column(Float, default=0.0)                       # Cost price
    total_value = Column(Float, default=0.0)

    transfer = relationship("StockTransfer", back_populates="items")

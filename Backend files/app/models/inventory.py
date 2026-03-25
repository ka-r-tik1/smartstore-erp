# SmartStore ERP — Inventory Models
# StockMovement = har stock in/out ka log (kab aaya, kab gaya, kitna, kyun)
# StockBatch = batch-wise stock with expiry date

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date, Text
from sqlalchemy.sql import func

from app.core.database import Base


class StockMovement(Base):
    """Har baar stock change ho — log rakh (audit trail)"""
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    movement_type = Column(String(20), nullable=False, index=True)
    # movement_type: "purchase_in" / "sale_out" / "return_in" / "damage_out" / "adjustment"
    qty = Column(Integer, nullable=False)                    # + ya - dono ho sakta hai
    stock_before = Column(Integer, nullable=False)           # Move se pehle kitna tha
    stock_after = Column(Integer, nullable=False)            # Move ke baad kitna hai
    reference = Column(String(100), nullable=True)           # Invoice number ya reason
    notes = Column(Text, nullable=True)                      # Extra note
    created_by = Column(String(100), nullable=True)          # Kisne kiya
    created_at = Column(DateTime, server_default=func.now(), index=True)


class StockBatch(Base):
    """Batch-wise stock — har batch ki alag expiry date"""
    __tablename__ = "stock_batches"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    batch_number = Column(String(50), nullable=True)         # Batch number from supplier
    qty = Column(Integer, default=0)                         # Is batch mein kitna bacha
    purchase_price = Column(Float, nullable=True)            # Is batch ka purchase price
    expiry_date = Column(Date, nullable=True, index=True)    # Expiry date
    received_date = Column(Date, nullable=True)               # Kab aaya
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

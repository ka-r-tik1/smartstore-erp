# SmartStore ERP — Product Model
# Ye table saare products store karega (Amul Butter, Tata Salt, Maggi, etc.)

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.sql import func

from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)       # Product ka naam
    name_mr = Column(String(200), nullable=True)                 # Marathi mein naam
    barcode = Column(String(50), unique=True, nullable=True, index=True)  # Barcode number
    hsn_code = Column(String(20), nullable=True)                 # GST HSN code
    category = Column(String(100), nullable=True, index=True)    # Category: Dairy, Snacks, etc.
    brand = Column(String(100), nullable=True)                   # Brand: Amul, Tata, etc.
    unit = Column(String(20), default="pcs")                     # Unit: pcs, kg, litre, box
    mrp = Column(Float, nullable=False)                          # MRP — Maximum Retail Price
    selling_price = Column(Float, nullable=False)                # Actual selling price
    purchase_price = Column(Float, nullable=True)                # Kitne mein kharida
    gst_rate = Column(Float, default=0.0)                        # GST % (0, 5, 12, 18, 28)
    stock_qty = Column(Integer, default=0)                       # Current stock
    reorder_level = Column(Integer, default=10)                  # Isse neeche jaaye toh alert
    is_active = Column(Boolean, default=True)                    # Active hai ya discontinued
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

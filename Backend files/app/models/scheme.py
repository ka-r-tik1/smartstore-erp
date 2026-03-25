# SmartStore ERP — Scheme/Offer Model (Phase 10)
# Schemes = offers jo customer ko milti hain (Buy 1 Get 1, % discount, flat off, combo)

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Date, Text
from sqlalchemy.sql import func

from app.core.database import Base


class Scheme(Base):
    """Dukaan ke schemes/offers — Buy 1 Get 1, % off, flat discount, combo deals"""
    __tablename__ = "schemes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)                    # Scheme ka naam: "Summer Sale 10% Off"
    scheme_type = Column(String(30), nullable=False, index=True)
    # scheme_type options:
    #   "percent_off"   — X% discount (e.g. 10% off)
    #   "flat_off"      — Rs X off (e.g. Rs 50 off)
    #   "buy_x_get_y"   — Buy X Get Y free (e.g. Buy 2 Get 1)
    #   "combo"         — Combo price for specific products

    # Discount values
    discount_percent = Column(Float, default=0.0)                 # % discount (for percent_off)
    discount_amount = Column(Float, default=0.0)                  # Flat Rs off (for flat_off)
    buy_qty = Column(Integer, default=0)                          # Buy X (for buy_x_get_y)
    get_qty = Column(Integer, default=0)                          # Get Y free (for buy_x_get_y)

    # Applicability — kis pe lagega
    apply_on = Column(String(30), default="all", index=True)
    # apply_on options: "all", "category", "brand", "product"
    apply_value = Column(String(200), nullable=True)              # Category name / Brand name / Product ID(s)

    # Minimum order condition
    min_order_amount = Column(Float, default=0.0)                 # Minimum bill amount for scheme
    min_qty = Column(Integer, default=0)                          # Minimum product qty for scheme

    # Validity
    start_date = Column(Date, nullable=False)                     # Scheme start date
    end_date = Column(Date, nullable=False)                       # Scheme end date
    is_active = Column(Boolean, default=True)                     # Active hai ya nahi

    description = Column(Text, nullable=True)                     # Scheme ki detail
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

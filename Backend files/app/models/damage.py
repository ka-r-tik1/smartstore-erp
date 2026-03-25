# SmartStore ERP — Damage & Wastage Model
# Damaged, expired, ya lost stock ka record
# Stock se minus hoga, P&L mein expense dikhega

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class DamageEntry(Base):
    """Damage/Wastage Entry — kharab ya expired maal ka record"""
    __tablename__ = "damage_entries"

    id = Column(Integer, primary_key=True, index=True)
    entry_number = Column(String(50), unique=True, nullable=False, index=True)  # DMG-2026-0001
    entry_date = Column(Date, nullable=False)
    damage_type = Column(String(30), nullable=False, index=True)  # damaged / expired / lost / stolen
    reason = Column(String(300), nullable=True)                   # Kaise hua
    total_loss_value = Column(Float, default=0.0)                 # Total nuksaan Rs mein
    status = Column(String(20), default="recorded")               # recorded / written_off / insured
    recorded_by = Column(String(100), nullable=True)
    approved_by = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    items = relationship("DamageItem", back_populates="damage_entry")


class DamageItem(Base):
    """Damage Entry mein kaunsa product kitna kharab hua"""
    __tablename__ = "damage_items"

    id = Column(Integer, primary_key=True, index=True)
    damage_id = Column(Integer, ForeignKey("damage_entries.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(200), nullable=False)
    qty_damaged = Column(Integer, nullable=False)
    cost_price = Column(Float, nullable=False)                    # Purchase price per unit
    loss_value = Column(Float, nullable=False)                    # qty × cost_price
    batch_number = Column(String(100), nullable=True)
    expiry_date = Column(Date, nullable=True)

    damage_entry = relationship("DamageEntry", back_populates="items")

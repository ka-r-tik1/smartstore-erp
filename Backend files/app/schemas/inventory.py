# SmartStore ERP — Inventory Schemas
# Stock movement log + batch with expiry

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


# Stock In — naya maal aaya (purchase/return)
class StockInRequest(BaseModel):
    product_id: int = Field(..., description="Product ka ID")
    qty: int = Field(..., gt=0, description="Kitna aaya")
    movement_type: str = Field("purchase_in", description="purchase_in / return_in / adjustment")
    batch_number: Optional[str] = Field(None, description="Batch number (supplier se)")
    purchase_price: Optional[float] = Field(None, ge=0, description="Is batch ka purchase price")
    expiry_date: Optional[date] = Field(None, description="Expiry date (YYYY-MM-DD)")
    reference: Optional[str] = Field(None, description="Invoice/PO number")
    notes: Optional[str] = None


# Stock Out — maal gaya (damage/wastage)
class StockOutRequest(BaseModel):
    product_id: int = Field(..., description="Product ka ID")
    qty: int = Field(..., gt=0, description="Kitna gaya")
    movement_type: str = Field("damage_out", description="damage_out / adjustment")
    reference: Optional[str] = Field(None, description="Reason ya reference")
    notes: Optional[str] = None


# Stock Movement Response
class StockMovementResponse(BaseModel):
    id: int
    product_id: int
    movement_type: str
    qty: int
    stock_before: int
    stock_after: int
    reference: Optional[str] = None
    notes: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# Stock Batch Response
class StockBatchResponse(BaseModel):
    id: int
    product_id: int
    batch_number: Optional[str] = None
    qty: int
    purchase_price: Optional[float] = None
    expiry_date: Optional[date] = None
    received_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# Low Stock Alert Response
class LowStockAlert(BaseModel):
    product_id: int
    product_name: str
    current_stock: int
    reorder_level: int
    shortage: int  # kitna kam hai


# Expiry Alert Response
class ExpiryAlert(BaseModel):
    batch_id: int
    product_id: int
    product_name: str
    batch_number: Optional[str] = None
    qty: int
    expiry_date: date
    days_left: int

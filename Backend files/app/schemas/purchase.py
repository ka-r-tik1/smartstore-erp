# SmartStore ERP — Purchase Order Schemas

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


# PO item
class POItemCreate(BaseModel):
    product_id: int = Field(..., description="Product ka ID")
    qty_ordered: int = Field(..., gt=0, description="Kitna mangwana hai")
    unit_price: float = Field(..., gt=0, description="Per unit purchase price")


# PO banane ke liye
class POCreate(BaseModel):
    supplier_id: int = Field(..., description="Supplier (dealer) ka ID")
    items: list[POItemCreate] = Field(..., min_length=1, description="Items list")
    expected_date: Optional[date] = Field(None, description="Expected delivery date")
    notes: Optional[str] = None


# PO receive — kitna mila
class POReceiveItem(BaseModel):
    po_item_id: int = Field(..., description="PO Item ka ID")
    qty_received: int = Field(..., ge=0, description="Kitna mila")
    batch_number: Optional[str] = Field(None, description="Batch number")
    expiry_date: Optional[date] = Field(None, description="Expiry date")


class POReceive(BaseModel):
    items: list[POReceiveItem] = Field(..., min_length=1)
    notes: Optional[str] = None


# PO Item Response
class POItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    qty_ordered: int
    qty_received: int
    unit_price: float
    gst_rate: float
    gst_amount: float
    total: float

    model_config = {"from_attributes": True}


# PO Response
class POResponse(BaseModel):
    id: int
    po_number: str
    supplier_id: int
    status: str
    subtotal: float
    gst_amount: float
    grand_total: float
    expected_date: Optional[date] = None
    received_date: Optional[date] = None
    notes: Optional[str] = None
    created_by: Optional[str] = None
    approved_by: Optional[str] = None
    created_at: Optional[datetime] = None
    items: list[POItemResponse] = []

    model_config = {"from_attributes": True}

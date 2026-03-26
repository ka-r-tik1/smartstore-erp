# SmartStore ERP — Order/POS Schemas
# Ye file define karti hai ki bill/order ka data kis format mein aayega/jaayega

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# Cart mein ek item — product_id + qty bhejo
class CartItem(BaseModel):
    product_id: int = Field(..., description="Product ka ID")
    qty: int = Field(..., gt=0, description="Kitne piece/kg chahiye")
    selling_price: Optional[float] = Field(None, ge=0, description="Batch-selected selling price (optional — overrides product default)")


# POS se bill banane ke liye — cart items + payment info
class POSBillCreate(BaseModel):
    items: list[CartItem] = Field(..., min_length=1, description="Cart mein items ki list")
    dealer_id: Optional[int] = Field(None, description="Dealer/Customer ka ID (optional)")
    payment_mode: str = Field("cash", description="cash / upi / card / udhaar")
    discount: float = Field(0.0, ge=0, description="Discount amount (Rs)")
    notes: Optional[str] = Field(None, description="Koi note likhna ho toh")


# Order item ka response
class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    qty: int
    unit_price: float
    gst_rate: float
    gst_amount: float
    total: float

    model_config = {"from_attributes": True}


# Full order/bill ka response
class OrderResponse(BaseModel):
    id: int
    invoice_number: str
    dealer_id: Optional[int] = None
    order_type: str
    subtotal: float
    gst_amount: float
    discount: float
    grand_total: float
    payment_mode: str
    payment_status: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    items: list[OrderItemResponse] = []

    model_config = {"from_attributes": True}

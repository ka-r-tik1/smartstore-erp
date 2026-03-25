# SmartStore ERP — Product Schemas
# Ye file define karti hai ki product ka data kis format mein aayega/jaayega

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# Product banane ke liye — ye fields chahiye
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Product ka naam")
    name_mr: Optional[str] = Field(None, max_length=200, description="Marathi mein naam")
    barcode: Optional[str] = Field(None, max_length=50, description="Barcode number")
    hsn_code: Optional[str] = Field(None, max_length=20, description="GST HSN code")
    category: Optional[str] = Field(None, max_length=100, description="Category: Dairy, Snacks, etc.")
    brand: Optional[str] = Field(None, max_length=100, description="Brand: Amul, Tata, etc.")
    unit: str = Field("pcs", description="Unit: pcs, kg, litre, box")
    mrp: float = Field(..., gt=0, description="MRP — Maximum Retail Price")
    selling_price: float = Field(..., gt=0, description="Actual selling price")
    purchase_price: Optional[float] = Field(None, ge=0, description="Kitne mein kharida")
    gst_rate: float = Field(0.0, ge=0, le=28, description="GST % (0, 5, 12, 18, 28)")
    stock_qty: int = Field(0, ge=0, description="Current stock")
    reorder_level: int = Field(10, ge=0, description="Isse neeche jaaye toh alert")


# Product update karne ke liye — sab optional hai, jo bhejo wo update hoga
class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    name_mr: Optional[str] = None
    barcode: Optional[str] = None
    hsn_code: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    unit: Optional[str] = None
    mrp: Optional[float] = Field(None, gt=0)
    selling_price: Optional[float] = Field(None, gt=0)
    purchase_price: Optional[float] = Field(None, ge=0)
    gst_rate: Optional[float] = Field(None, ge=0, le=28)
    stock_qty: Optional[int] = Field(None, ge=0)
    reorder_level: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


# Product ka response — ye client ko dikhega
class ProductResponse(BaseModel):
    id: int
    name: str
    name_mr: Optional[str] = None
    barcode: Optional[str] = None
    hsn_code: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    unit: str
    mrp: float
    selling_price: float
    purchase_price: Optional[float] = None
    gst_rate: float
    stock_qty: int
    reorder_level: int
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

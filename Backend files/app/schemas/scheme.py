# SmartStore ERP — Scheme Schemas (Phase 10)
# Request/Response format for schemes/offers

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


class SchemeCreate(BaseModel):
    """Naya scheme banao"""
    name: str = Field(..., min_length=1, max_length=200, description="Scheme ka naam")
    scheme_type: str = Field(..., description="percent_off / flat_off / buy_x_get_y / combo")
    discount_percent: float = Field(0.0, ge=0, le=100, description="% discount")
    discount_amount: float = Field(0.0, ge=0, description="Flat Rs off")
    buy_qty: int = Field(0, ge=0, description="Buy X qty")
    get_qty: int = Field(0, ge=0, description="Get Y free")
    apply_on: str = Field("all", description="all / category / brand / product")
    apply_value: Optional[str] = Field(None, description="Category/Brand name ya Product ID")
    min_order_amount: float = Field(0.0, ge=0, description="Minimum bill amount")
    min_qty: int = Field(0, ge=0, description="Minimum qty for scheme")
    start_date: date = Field(..., description="Scheme start date")
    end_date: date = Field(..., description="Scheme end date")
    description: Optional[str] = None


class SchemeUpdate(BaseModel):
    """Scheme update karo — jo bhejo wo update hoga"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    scheme_type: Optional[str] = None
    discount_percent: Optional[float] = Field(None, ge=0, le=100)
    discount_amount: Optional[float] = Field(None, ge=0)
    buy_qty: Optional[int] = Field(None, ge=0)
    get_qty: Optional[int] = Field(None, ge=0)
    apply_on: Optional[str] = None
    apply_value: Optional[str] = None
    min_order_amount: Optional[float] = Field(None, ge=0)
    min_qty: Optional[int] = Field(None, ge=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


class SchemeResponse(BaseModel):
    """Scheme ka response"""
    id: int
    name: str
    scheme_type: str
    discount_percent: float
    discount_amount: float
    buy_qty: int
    get_qty: int
    apply_on: str
    apply_value: Optional[str] = None
    min_order_amount: float
    min_qty: int
    start_date: date
    end_date: date
    is_active: bool
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

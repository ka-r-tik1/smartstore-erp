# SmartStore ERP — Dealer Schemas
# Dealer CRUD + Udhaar payment collection

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# Dealer banane ke liye
class DealerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Dealer ka naam")
    phone: Optional[str] = Field(None, max_length=15, description="Phone number")
    email: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    gstin: Optional[str] = Field(None, max_length=15, description="GSTIN (if registered)")
    credit_limit: float = Field(0.0, ge=0, description="Max udhaar allowed (Rs)")
    dealer_type: str = Field("customer", description="supplier / customer / both")


# Dealer update
class DealerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    gstin: Optional[str] = None
    credit_limit: Optional[float] = Field(None, ge=0)
    dealer_type: Optional[str] = None
    is_active: Optional[bool] = None


# Dealer response
class DealerResponse(BaseModel):
    id: int
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    gstin: Optional[str] = None
    credit_limit: float
    outstanding: float
    dealer_type: str
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# Payment collect karne ke liye
class PaymentCollect(BaseModel):
    dealer_id: int = Field(..., description="Dealer ka ID")
    amount: float = Field(..., gt=0, description="Kitna collect kiya (Rs)")
    payment_mode: str = Field("cash", description="cash / upi / card")
    reference: Optional[str] = Field(None, description="Receipt number ya note")
    notes: Optional[str] = None


# Payment response
class PaymentResponse(BaseModel):
    id: int
    dealer_id: int
    amount: float
    payment_mode: str
    reference: Optional[str] = None
    notes: Optional[str] = None
    outstanding_before: float
    outstanding_after: float
    collected_by: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

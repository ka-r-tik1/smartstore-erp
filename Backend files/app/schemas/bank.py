# SmartStore ERP — Payment Ledger + Bank Recon Schemas

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


# Manual ledger entry (expense/manual adjustment)
class LedgerEntryCreate(BaseModel):
    entry_type: str = Field(..., description="expense / refund / manual_in / manual_out")
    amount: float = Field(..., gt=0, description="Amount in Rs")
    payment_mode: str = Field("cash", description="cash / upi / card / bank")
    description: str = Field(..., description="Kya tha ye payment")
    dealer_id: Optional[int] = None
    entry_date: Optional[date] = Field(None, description="Date (default: today)")


# Ledger response
class LedgerResponse(BaseModel):
    id: int
    entry_type: str
    amount: float
    payment_mode: str
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    reference_number: Optional[str] = None
    dealer_id: Optional[int] = None
    dealer_name: Optional[str] = None
    description: Optional[str] = None
    entry_date: date
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# Bank transaction (from CSV row)
class BankTxnCreate(BaseModel):
    txn_date: date
    description: Optional[str] = None
    reference_number: Optional[str] = None
    debit: float = Field(0.0, ge=0)
    credit: float = Field(0.0, ge=0)
    balance: Optional[float] = None


# Bank transaction response
class BankTxnResponse(BaseModel):
    id: int
    txn_date: date
    description: Optional[str] = None
    reference_number: Optional[str] = None
    debit: float
    credit: float
    balance: Optional[float] = None
    is_matched: bool
    matched_ledger_id: Optional[int] = None
    match_notes: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# Manual match request
class ManualMatch(BaseModel):
    bank_txn_id: int = Field(..., description="Bank transaction ID")
    ledger_id: int = Field(..., description="Ledger entry ID")
    notes: Optional[str] = None

# SmartStore ERP — Payment Ledger + Bank Transaction Models
# PaymentLedger = har paisa in/out ka master log
# BankTransaction = bank CSV se upload, auto-match with orders

from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Text, Boolean
from sqlalchemy.sql import func

from app.core.database import Base


class PaymentLedger(Base):
    """Master payment log — har paisa in/out yahan record hota hai"""
    __tablename__ = "payment_ledger"

    id = Column(Integer, primary_key=True, index=True)
    entry_type = Column(String(20), nullable=False, index=True)
    # entry_type: "sale_in" / "purchase_out" / "udhaar_collect" / "expense" / "refund"
    amount = Column(Float, nullable=False)
    payment_mode = Column(String(30), nullable=False, index=True)  # cash / upi / card / bank
    reference_type = Column(String(30), nullable=True)   # order / payment / expense / manual
    reference_id = Column(Integer, nullable=True)        # Order ID / Payment ID
    reference_number = Column(String(100), nullable=True) # Invoice/Receipt number
    dealer_id = Column(Integer, nullable=True)
    dealer_name = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    entry_date = Column(Date, nullable=False, index=True)
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class BankTransaction(Base):
    """Bank statement se upload ki gayi transactions"""
    __tablename__ = "bank_transactions"

    id = Column(Integer, primary_key=True, index=True)
    txn_date = Column(Date, nullable=False, index=True)
    description = Column(String(500), nullable=True)       # Bank statement description
    reference_number = Column(String(100), nullable=True)   # UTR / Cheque number
    debit = Column(Float, default=0.0)                      # Paisa gaya
    credit = Column(Float, default=0.0)                     # Paisa aaya
    balance = Column(Float, nullable=True)                  # Closing balance
    is_matched = Column(Boolean, default=False, index=True) # Matched with our records?
    matched_ledger_id = Column(Integer, nullable=True)      # Kis ledger entry se match hua
    match_notes = Column(String(200), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

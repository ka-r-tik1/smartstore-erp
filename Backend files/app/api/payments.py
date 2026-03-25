# SmartStore ERP — Payments Ledger API
# Master payment log, daily report, cash flow, expense tracking

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import date, datetime

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.bank import PaymentLedger
from app.models.dealer import Dealer
from app.models.user import User
from app.schemas.bank import LedgerEntryCreate, LedgerResponse

router = APIRouter(prefix="/payments", tags=["Payments & Ledger"])


# ──────────────────────────────────────
# 1. Add Manual Entry (expense/refund/manual)
# ──────────────────────────────────────
@router.post("/entry", response_model=LedgerResponse, status_code=201)
def add_ledger_entry(
    data: LedgerEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner", "staff"]))
):
    """Manual payment entry — expense, refund, adjustment"""

    entry_date = data.entry_date or date.today()

    dealer_name = None
    if data.dealer_id:
        dealer = db.query(Dealer).filter(Dealer.id == data.dealer_id).first()
        dealer_name = dealer.name if dealer else None

    entry = PaymentLedger(
        entry_type=data.entry_type,
        amount=data.amount,
        payment_mode=data.payment_mode,
        reference_type="manual",
        description=data.description,
        dealer_id=data.dealer_id,
        dealer_name=dealer_name,
        entry_date=entry_date,
        created_by=current_user.username
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


# ──────────────────────────────────────
# 2. Ledger List (all entries with filters)
# ──────────────────────────────────────
@router.get("/ledger", response_model=list[LedgerResponse])
def list_ledger(
    entry_type: Optional[str] = Query(None, description="sale_in / purchase_out / udhaar_collect / expense / refund"),
    payment_mode: Optional[str] = Query(None, description="cash / upi / card / bank"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Payment ledger — saare entries with filters"""

    query = db.query(PaymentLedger)

    if entry_type:
        query = query.filter(PaymentLedger.entry_type == entry_type)
    if payment_mode:
        query = query.filter(PaymentLedger.payment_mode == payment_mode)
    if date_from:
        query = query.filter(PaymentLedger.entry_date >= date_from)
    if date_to:
        query = query.filter(PaymentLedger.entry_date <= date_to)

    entries = query.order_by(PaymentLedger.entry_date.desc(), PaymentLedger.id.desc()).offset(skip).limit(limit).all()
    return entries


# ──────────────────────────────────────
# 3. Daily Cash Report
# ──────────────────────────────────────
@router.get("/daily-report")
def daily_report(
    report_date: Optional[date] = Query(None, description="Kis din ka report (default: today)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """Ek din ka full cash report — kitna aaya, kitna gaya"""

    target_date = report_date or date.today()

    entries = db.query(PaymentLedger).filter(
        PaymentLedger.entry_date == target_date
    ).all()

    # Money in types
    money_in_types = ["sale_in", "udhaar_collect", "manual_in"]
    # Money out types
    money_out_types = ["purchase_out", "expense", "refund", "manual_out"]

    total_in = sum(e.amount for e in entries if e.entry_type in money_in_types)
    total_out = sum(e.amount for e in entries if e.entry_type in money_out_types)

    # Mode-wise breakup (money in only)
    cash_in = sum(e.amount for e in entries if e.entry_type in money_in_types and e.payment_mode == "cash")
    upi_in = sum(e.amount for e in entries if e.entry_type in money_in_types and e.payment_mode == "upi")
    card_in = sum(e.amount for e in entries if e.entry_type in money_in_types and e.payment_mode == "card")

    return {
        "date": str(target_date),
        "total_entries": len(entries),
        "total_money_in": round(total_in, 2),
        "total_money_out": round(total_out, 2),
        "net_cash_flow": round(total_in - total_out, 2),
        "mode_wise_in": {
            "cash": round(cash_in, 2),
            "upi": round(upi_in, 2),
            "card": round(card_in, 2)
        }
    }


# ──────────────────────────────────────
# 4. Cash Flow Summary (date range)
# ──────────────────────────────────────
@router.get("/cash-flow")
def cash_flow(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """Date range ka cash flow — total in, out, net"""

    query = db.query(PaymentLedger)
    if date_from:
        query = query.filter(PaymentLedger.entry_date >= date_from)
    if date_to:
        query = query.filter(PaymentLedger.entry_date <= date_to)

    entries = query.all()

    money_in_types = ["sale_in", "udhaar_collect", "manual_in"]
    money_out_types = ["purchase_out", "expense", "refund", "manual_out"]

    total_in = sum(e.amount for e in entries if e.entry_type in money_in_types)
    total_out = sum(e.amount for e in entries if e.entry_type in money_out_types)

    # Type-wise breakup
    type_breakup = {}
    for e in entries:
        if e.entry_type not in type_breakup:
            type_breakup[e.entry_type] = 0
        type_breakup[e.entry_type] += e.amount

    return {
        "period": f"{date_from or 'start'} to {date_to or 'today'}",
        "total_money_in": round(total_in, 2),
        "total_money_out": round(total_out, 2),
        "net_cash_flow": round(total_in - total_out, 2),
        "type_breakup": {k: round(v, 2) for k, v in type_breakup.items()}
    }

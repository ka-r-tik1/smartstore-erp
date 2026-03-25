# SmartStore ERP — Bank Reconciliation API
# CSV upload, auto-match with ledger, manual match, recon report

import csv
import io
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import date, datetime

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.bank import BankTransaction, PaymentLedger
from app.models.user import User
from app.schemas.bank import BankTxnCreate, BankTxnResponse, ManualMatch

router = APIRouter(prefix="/bank", tags=["Bank Reconciliation"])


# ──────────────────────────────────────
# 1. Upload Bank Statement CSV
# ──────────────────────────────────────
@router.post("/upload-csv")
async def upload_bank_csv(
    file: UploadFile = File(..., description="Bank statement CSV file"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """Bank statement CSV upload karo — transactions auto-import"""

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Sirf CSV file upload karo")

    content = await file.read()
    text = content.decode("utf-8-sig")  # Handle BOM
    reader = csv.DictReader(io.StringIO(text))

    imported = 0
    skipped = 0
    errors = []

    for row_num, row in enumerate(reader, start=2):
        try:
            # Flexible column mapping
            txn_date_str = row.get("Date") or row.get("date") or row.get("Txn Date") or row.get("Transaction Date") or ""
            description = row.get("Description") or row.get("description") or row.get("Narration") or row.get("Particulars") or ""
            ref = row.get("Reference") or row.get("reference") or row.get("Ref No") or row.get("UTR") or ""
            debit = float(row.get("Debit") or row.get("debit") or row.get("Withdrawal") or 0)
            credit = float(row.get("Credit") or row.get("credit") or row.get("Deposit") or 0)
            balance = row.get("Balance") or row.get("balance") or row.get("Closing Balance")
            balance = float(balance) if balance else None

            # Parse date (try multiple formats)
            txn_date = None
            for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y"]:
                try:
                    txn_date = datetime.strptime(txn_date_str.strip(), fmt).date()
                    break
                except ValueError:
                    continue

            if not txn_date:
                errors.append(f"Row {row_num}: Date parse error '{txn_date_str}'")
                skipped += 1
                continue

            if debit == 0 and credit == 0:
                skipped += 1
                continue

            txn = BankTransaction(
                txn_date=txn_date,
                description=description.strip(),
                reference_number=ref.strip() if ref else None,
                debit=debit,
                credit=credit,
                balance=balance
            )
            db.add(txn)
            imported += 1

        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")
            skipped += 1

    db.commit()

    return {
        "message": f"CSV processed: {imported} imported, {skipped} skipped",
        "imported": imported,
        "skipped": skipped,
        "errors": errors[:10]  # Max 10 errors dikhao
    }


# ──────────────────────────────────────
# 2. Add single bank transaction manually
# ──────────────────────────────────────
@router.post("/transaction", response_model=BankTxnResponse, status_code=201)
def add_bank_transaction(
    data: BankTxnCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """Ek bank transaction manually add karo"""
    txn = BankTransaction(**data.model_dump())
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


# ──────────────────────────────────────
# 3. List Bank Transactions
# ──────────────────────────────────────
@router.get("/transactions", response_model=list[BankTxnResponse])
def list_bank_transactions(
    matched: Optional[bool] = Query(None, description="True=matched, False=unmatched"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """Bank transactions list — matched/unmatched filter"""

    query = db.query(BankTransaction)

    if matched is not None:
        query = query.filter(BankTransaction.is_matched == matched)
    if date_from:
        query = query.filter(BankTransaction.txn_date >= date_from)
    if date_to:
        query = query.filter(BankTransaction.txn_date <= date_to)

    txns = query.order_by(BankTransaction.txn_date.desc()).offset(skip).limit(limit).all()
    return txns


# ──────────────────────────────────────
# 4. Auto-Match bank transactions with ledger
# ──────────────────────────────────────
@router.post("/auto-match")
def auto_match(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """Unmatched bank transactions ko ledger entries se auto-match karo (amount + date)"""

    unmatched = db.query(BankTransaction).filter(
        BankTransaction.is_matched == False
    ).all()

    matched_count = 0

    for txn in unmatched:
        amount = txn.credit if txn.credit > 0 else txn.debit

        # Ledger mein same amount + same date dhundho
        ledger_entry = db.query(PaymentLedger).filter(
            PaymentLedger.amount == amount,
            PaymentLedger.entry_date == txn.txn_date
        ).first()

        if ledger_entry:
            # Check if already matched to another txn
            already = db.query(BankTransaction).filter(
                BankTransaction.matched_ledger_id == ledger_entry.id,
                BankTransaction.is_matched == True
            ).first()

            if not already:
                txn.is_matched = True
                txn.matched_ledger_id = ledger_entry.id
                txn.match_notes = f"Auto-matched: {ledger_entry.entry_type} - {ledger_entry.description or ''}"
                matched_count += 1

    db.commit()

    remaining = db.query(BankTransaction).filter(BankTransaction.is_matched == False).count()

    return {
        "message": f"{matched_count} transactions auto-matched",
        "matched": matched_count,
        "remaining_unmatched": remaining
    }


# ──────────────────────────────────────
# 5. Manual Match
# ──────────────────────────────────────
@router.post("/manual-match")
def manual_match(
    data: ManualMatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """Bank transaction ko manually ledger entry se match karo"""

    txn = db.query(BankTransaction).filter(BankTransaction.id == data.bank_txn_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Bank transaction nahi mili")

    ledger = db.query(PaymentLedger).filter(PaymentLedger.id == data.ledger_id).first()
    if not ledger:
        raise HTTPException(status_code=404, detail="Ledger entry nahi mili")

    txn.is_matched = True
    txn.matched_ledger_id = ledger.id
    txn.match_notes = data.notes or f"Manual match by {current_user.username}"
    db.commit()

    return {"message": f"Bank txn #{data.bank_txn_id} matched with ledger #{data.ledger_id}"}


# ──────────────────────────────────────
# 6. Reconciliation Summary
# ──────────────────────────────────────
@router.get("/recon-summary")
def recon_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """Bank reconciliation summary — matched vs unmatched"""

    total = db.query(BankTransaction).count()
    matched = db.query(BankTransaction).filter(BankTransaction.is_matched == True).count()
    unmatched = total - matched

    total_bank_credit = db.query(func.sum(BankTransaction.credit)).scalar() or 0
    total_bank_debit = db.query(func.sum(BankTransaction.debit)).scalar() or 0

    total_ledger_in = db.query(func.sum(PaymentLedger.amount)).filter(
        PaymentLedger.entry_type.in_(["sale_in", "udhaar_collect", "manual_in"])
    ).scalar()
    total_ledger_in = total_ledger_in or 0

    total_ledger_out = db.query(func.sum(PaymentLedger.amount)).filter(
        PaymentLedger.entry_type.in_(["purchase_out", "expense", "refund", "manual_out"])
    ).scalar()
    total_ledger_out = total_ledger_out or 0

    return {
        "bank_transactions": {
            "total": total,
            "matched": matched,
            "unmatched": unmatched,
            "match_rate": f"{round(matched/total*100, 1)}%" if total > 0 else "0%"
        },
        "bank_totals": {
            "total_credit": round(total_bank_credit, 2),
            "total_debit": round(total_bank_debit, 2),
            "net": round(total_bank_credit - total_bank_debit, 2)
        },
        "ledger_totals": {
            "total_in": round(total_ledger_in, 2),
            "total_out": round(total_ledger_out, 2),
            "net": round(total_ledger_in - total_ledger_out, 2)
        },
        "difference": round((total_bank_credit - total_bank_debit) - (total_ledger_in - total_ledger_out), 2)
    }

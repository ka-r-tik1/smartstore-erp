# SmartStore ERP — Dealers + Udhaar API
# Dealer CRUD + Udhaar payment collection + Outstanding tracking

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.dealer import Dealer
from app.models.order import Order
from app.models.payment import Payment
from app.models.user import User
from app.schemas.dealer import (
    DealerCreate, DealerUpdate, DealerResponse,
    PaymentCollect, PaymentResponse
)

router = APIRouter(prefix="/dealers", tags=["Dealers & Udhaar"])


# ──────────────────────────────────────
# 1. Dealer Add karo
# ──────────────────────────────────────
@router.post("/", response_model=DealerResponse, status_code=201)
def add_dealer(
    dealer: DealerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner", "staff"]))
):
    """Naya dealer/customer add karo"""

    # Phone duplicate check
    if dealer.phone:
        existing = db.query(Dealer).filter(Dealer.phone == dealer.phone).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Phone '{dealer.phone}' already exists — {existing.name}")

    db_dealer = Dealer(**dealer.model_dump())
    db.add(db_dealer)
    db.commit()
    db.refresh(db_dealer)
    return db_dealer


# ──────────────────────────────────────
# 2. Dealers list (search + filter)
# ──────────────────────────────────────
@router.get("/", response_model=list[DealerResponse])
def list_dealers(
    search: Optional[str] = Query(None, description="Name ya phone se search"),
    dealer_type: Optional[str] = Query(None, description="supplier / customer / both"),
    has_outstanding: Optional[bool] = Query(None, description="Sirf udhaar wale dikhao"),
    active_only: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dealers ki list — search, filter, udhaar filter"""

    query = db.query(Dealer)

    if active_only:
        query = query.filter(Dealer.is_active == True)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Dealer.name.ilike(search_term)) |
            (Dealer.phone.ilike(search_term))
        )

    if dealer_type:
        query = query.filter(Dealer.dealer_type == dealer_type)

    if has_outstanding is True:
        query = query.filter(Dealer.outstanding > 0)

    dealers = query.order_by(Dealer.name).offset(skip).limit(limit).all()
    return dealers


# ──────────────────────────────────────
# 3. Dealer detail
# ──────────────────────────────────────
@router.get("/{dealer_id}", response_model=DealerResponse)
def get_dealer(
    dealer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dealer ki full detail"""
    dealer = db.query(Dealer).filter(Dealer.id == dealer_id).first()
    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer nahi mila")
    return dealer


# ──────────────────────────────────────
# 4. Dealer Update
# ──────────────────────────────────────
@router.put("/{dealer_id}", response_model=DealerResponse)
def update_dealer(
    dealer_id: int,
    dealer_update: DealerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner", "staff"]))
):
    """Dealer update karo"""
    dealer = db.query(Dealer).filter(Dealer.id == dealer_id).first()
    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer nahi mila")

    update_data = dealer_update.model_dump(exclude_unset=True)

    # Phone duplicate check
    if "phone" in update_data and update_data["phone"]:
        existing = db.query(Dealer).filter(
            Dealer.phone == update_data["phone"],
            Dealer.id != dealer_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Phone '{update_data['phone']}' already exists")

    for key, value in update_data.items():
        setattr(dealer, key, value)

    db.commit()
    db.refresh(dealer)
    return dealer


# ──────────────────────────────────────
# 5. Udhaar Payment Collect karo
# ──────────────────────────────────────
@router.post("/collect-payment", response_model=PaymentResponse, status_code=201)
def collect_payment(
    data: PaymentCollect,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner", "cashier"]))
):
    """Udhaar ka paisa vasool karo — outstanding auto-update"""

    dealer = db.query(Dealer).filter(Dealer.id == data.dealer_id).first()
    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer nahi mila")

    if dealer.outstanding <= 0:
        raise HTTPException(status_code=400, detail=f"{dealer.name} ka koi udhaar baaki nahi hai")

    if data.amount > dealer.outstanding:
        raise HTTPException(
            status_code=400,
            detail=f"Amount Rs {data.amount} > Outstanding Rs {dealer.outstanding}. Zyada nahi le sakte"
        )

    outstanding_before = dealer.outstanding
    dealer.outstanding -= data.amount
    outstanding_after = dealer.outstanding

    # Update related orders if fully paid
    if dealer.outstanding == 0:
        pending_orders = db.query(Order).filter(
            Order.dealer_id == dealer.id,
            Order.payment_status == "pending"
        ).all()
        for order in pending_orders:
            order.payment_status = "paid"

    payment = Payment(
        dealer_id=data.dealer_id,
        amount=data.amount,
        payment_mode=data.payment_mode,
        reference=data.reference,
        notes=data.notes,
        outstanding_before=outstanding_before,
        outstanding_after=outstanding_after,
        collected_by=current_user.username
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


# ──────────────────────────────────────
# 6. Payment History (dealer-wise)
# ──────────────────────────────────────
@router.get("/{dealer_id}/payments", response_model=list[PaymentResponse])
def payment_history(
    dealer_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dealer ki payment history — kab kitna diya"""
    dealer = db.query(Dealer).filter(Dealer.id == dealer_id).first()
    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer nahi mila")

    payments = db.query(Payment).filter(
        Payment.dealer_id == dealer_id
    ).order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()

    return payments


# ──────────────────────────────────────
# 7. Dealer ke orders (khata)
# ──────────────────────────────────────
@router.get("/{dealer_id}/orders")
def dealer_orders(
    dealer_id: int,
    payment_status: Optional[str] = Query(None, description="paid / pending"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dealer ke saare orders — udhaar khata"""
    dealer = db.query(Dealer).filter(Dealer.id == dealer_id).first()
    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer nahi mila")

    query = db.query(Order).filter(Order.dealer_id == dealer_id)

    if payment_status:
        query = query.filter(Order.payment_status == payment_status)

    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()

    return [{
        "id": o.id,
        "invoice_number": o.invoice_number,
        "grand_total": o.grand_total,
        "payment_mode": o.payment_mode,
        "payment_status": o.payment_status,
        "created_at": str(o.created_at)
    } for o in orders]


# ──────────────────────────────────────
# 8. Outstanding Summary — sabke udhaar ka overview
# ──────────────────────────────────────
@router.get("/summary/outstanding")
def outstanding_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """Total udhaar kitna baaki hai — sabka combined"""

    dealers_with_udhaar = db.query(Dealer).filter(
        Dealer.outstanding > 0,
        Dealer.is_active == True
    ).order_by(Dealer.outstanding.desc()).all()

    total_outstanding = sum(d.outstanding for d in dealers_with_udhaar)

    return {
        "total_outstanding": round(total_outstanding, 2),
        "dealers_count": len(dealers_with_udhaar),
        "top_defaulters": [{
            "id": d.id,
            "name": d.name,
            "phone": d.phone,
            "outstanding": d.outstanding,
            "credit_limit": d.credit_limit
        } for d in dealers_with_udhaar[:10]]
    }

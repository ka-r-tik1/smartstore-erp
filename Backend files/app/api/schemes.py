# SmartStore ERP — Schemes/Offers API (Phase 10)
# Scheme banao, list karo, update karo, delete karo, bill pe check karo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.scheme import Scheme
from app.models.product import Product
from app.models.user import User
from app.schemas.scheme import SchemeCreate, SchemeUpdate, SchemeResponse

router = APIRouter(prefix="/schemes", tags=["Schemes & Offers"])


# ──────────────────────────────────────
# 1. Scheme Create karo (Owner only)
# ──────────────────────────────────────
@router.post("/", response_model=SchemeResponse, status_code=201)
def create_scheme(
    scheme: SchemeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """Naya scheme/offer banao — sirf Owner kar sakta hai"""

    # Validation — scheme_type ke hisab se required fields check
    if scheme.scheme_type == "percent_off" and scheme.discount_percent <= 0:
        raise HTTPException(status_code=400, detail="percent_off mein discount_percent dena zaroori hai")
    if scheme.scheme_type == "flat_off" and scheme.discount_amount <= 0:
        raise HTTPException(status_code=400, detail="flat_off mein discount_amount dena zaroori hai")
    if scheme.scheme_type == "buy_x_get_y" and (scheme.buy_qty <= 0 or scheme.get_qty <= 0):
        raise HTTPException(status_code=400, detail="buy_x_get_y mein buy_qty aur get_qty dono zaroori hain")

    if scheme.end_date < scheme.start_date:
        raise HTTPException(status_code=400, detail="end_date start_date se pehle nahi ho sakti")

    db_scheme = Scheme(**scheme.model_dump())
    db.add(db_scheme)
    db.commit()
    db.refresh(db_scheme)
    return db_scheme


# ──────────────────────────────────────
# 2. Saare Schemes list karo
# ──────────────────────────────────────
@router.get("/", response_model=list[SchemeResponse])
def list_schemes(
    active_only: bool = Query(True, description="Sirf active schemes dikhao"),
    scheme_type: Optional[str] = Query(None, description="percent_off / flat_off / buy_x_get_y / combo"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Saare schemes ki list — filter by type, active status"""

    query = db.query(Scheme)

    if active_only:
        today = date.today()
        query = query.filter(
            Scheme.is_active == True,
            Scheme.start_date <= today,
            Scheme.end_date >= today
        )

    if scheme_type:
        query = query.filter(Scheme.scheme_type == scheme_type)

    schemes = query.order_by(Scheme.created_at.desc()).offset(skip).limit(limit).all()
    return schemes


# ──────────────────────────────────────
# 3. Ek Scheme ki detail
# ──────────────────────────────────────
@router.get("/{scheme_id}", response_model=SchemeResponse)
def get_scheme(
    scheme_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Scheme ki full detail by ID"""
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme nahi mili")
    return scheme


# ──────────────────────────────────────
# 4. Scheme Update karo (Owner only)
# ──────────────────────────────────────
@router.put("/{scheme_id}", response_model=SchemeResponse)
def update_scheme(
    scheme_id: int,
    scheme_update: SchemeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """Scheme update karo — Owner only"""
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme nahi mili")

    update_data = scheme_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(scheme, key, value)

    db.commit()
    db.refresh(scheme)
    return scheme


# ──────────────────────────────────────
# 5. Scheme Delete karo (Soft delete — Owner only)
# ──────────────────────────────────────
@router.delete("/{scheme_id}")
def delete_scheme(
    scheme_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """Scheme deactivate karo — soft delete"""
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme nahi mili")

    scheme.is_active = False
    db.commit()
    return {"message": f"Scheme '{scheme.name}' deactivated", "id": scheme_id}


# ──────────────────────────────────────
# 6. Check applicable schemes for a product
# ──────────────────────────────────────
@router.get("/check/{product_id}")
def check_product_schemes(
    product_id: int,
    qty: int = Query(1, ge=1, description="Kitni qty le raha hai"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ek product pe kaunse schemes lag sakte hain — qty ke hisab se"""

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product nahi mila")

    today = date.today()
    active_schemes = db.query(Scheme).filter(
        Scheme.is_active == True,
        Scheme.start_date <= today,
        Scheme.end_date >= today
    ).all()

    applicable = []
    for scheme in active_schemes:
        matches = False

        if scheme.apply_on == "all":
            matches = True
        elif scheme.apply_on == "category" and product.category:
            matches = scheme.apply_value and scheme.apply_value.lower() == product.category.lower()
        elif scheme.apply_on == "brand" and product.brand:
            matches = scheme.apply_value and scheme.apply_value.lower() == product.brand.lower()
        elif scheme.apply_on == "product":
            matches = scheme.apply_value and str(product_id) in scheme.apply_value.split(",")

        if not matches:
            continue

        # Min qty check
        if scheme.min_qty > 0 and qty < scheme.min_qty:
            continue

        # Calculate discount for this product
        item_total = product.selling_price * qty
        discount = 0.0
        free_qty = 0

        if scheme.scheme_type == "percent_off":
            discount = round(item_total * scheme.discount_percent / 100, 2)
        elif scheme.scheme_type == "flat_off":
            discount = min(scheme.discount_amount, item_total)
        elif scheme.scheme_type == "buy_x_get_y":
            if qty >= scheme.buy_qty:
                sets = qty // scheme.buy_qty
                free_qty = sets * scheme.get_qty
                discount = round(free_qty * product.selling_price, 2)

        if discount > 0 or free_qty > 0:
            applicable.append({
                "scheme_id": scheme.id,
                "scheme_name": scheme.name,
                "scheme_type": scheme.scheme_type,
                "discount": discount,
                "free_qty": free_qty,
                "description": scheme.description
            })

    return {
        "product_id": product_id,
        "product_name": product.name,
        "qty": qty,
        "original_total": round(product.selling_price * qty, 2),
        "applicable_schemes": applicable
    }


# ──────────────────────────────────────
# 7. Scheme Report — kitna discount diya total
# ──────────────────────────────────────
@router.get("/report/summary")
def scheme_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """Scheme summary — kitne active, expired, upcoming schemes hain"""

    today = date.today()
    all_schemes = db.query(Scheme).all()

    active = [s for s in all_schemes if s.is_active and s.start_date <= today <= s.end_date]
    expired = [s for s in all_schemes if s.end_date < today]
    upcoming = [s for s in all_schemes if s.start_date > today and s.is_active]
    deactivated = [s for s in all_schemes if not s.is_active]

    return {
        "total_schemes": len(all_schemes),
        "active_now": len(active),
        "expired": len(expired),
        "upcoming": len(upcoming),
        "deactivated": len(deactivated),
        "active_schemes": [{"id": s.id, "name": s.name, "type": s.scheme_type,
                           "end_date": str(s.end_date)} for s in active]
    }

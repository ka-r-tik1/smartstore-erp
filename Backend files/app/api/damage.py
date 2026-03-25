# SmartStore ERP — Damage & Wastage API
# Damaged, expired, lost, stolen stock ka record
# Stock minus hoga, loss report mein dikhega

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.product import Product
from app.models.damage import DamageEntry, DamageItem
from app.models.inventory import StockMovement
from app.models.user import User

router = APIRouter(prefix="/damage", tags=["Damage & Wastage"])


# ─── Pydantic Schemas ───────────────────────────────────────


class DamageItemIn(BaseModel):
    product_id: int
    qty_damaged: int
    cost_price: float
    batch_number: Optional[str] = None
    expiry_date: Optional[date] = None


class DamageEntryCreate(BaseModel):
    entry_date: date
    damage_type: str  # damaged / expired / lost / stolen
    reason: Optional[str] = None
    items: List[DamageItemIn]
    notes: Optional[str] = None


# ─── Helper ─────────────────────────────────────────────────


def gen_damage_number(db: Session) -> str:
    year = datetime.now().year
    prefix = f"DMG-{year}-"
    last = db.query(DamageEntry).filter(
        DamageEntry.entry_number.like(f"{prefix}%")
    ).order_by(DamageEntry.id.desc()).first()
    num = (int(last.entry_number.split("-")[-1]) + 1) if last else 1
    return f"{prefix}{num:04d}"


# ──────────────────────────────────────
# 1. Record Damage Entry
# ──────────────────────────────────────
@router.post("/", status_code=201)
def record_damage(
    data: DamageEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner", "staff"]))
):
    """Damage ya wastage record karo — stock minus hoga"""

    valid_types = ["damaged", "expired", "lost", "stolen"]
    if data.damage_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"damage_type must be: {', '.join(valid_types)}")

    entry_number = gen_damage_number(db)
    items_data = []
    total_loss = 0.0

    for item in data.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product ID {item.product_id} nahi mila")

        if product.stock_qty < item.qty_damaged:
            raise HTTPException(
                status_code=400,
                detail=f"{product.name}: stock sirf {product.stock_qty} hai, {item.qty_damaged} damage record nahi ho sakta"
            )

        loss_value = round(item.cost_price * item.qty_damaged, 2)
        items_data.append({
            "product": product,
            "damage_item": item,
            "loss_value": loss_value
        })
        total_loss += loss_value

    entry = DamageEntry(
        entry_number=entry_number,
        entry_date=data.entry_date,
        damage_type=data.damage_type,
        reason=data.reason,
        total_loss_value=round(total_loss, 2),
        status="recorded",
        recorded_by=current_user.username,
        notes=data.notes
    )

    db.add(entry)
    db.flush()

    stock_updates = []

    for d in items_data:
        di = DamageItem(
            damage_id=entry.id,
            product_id=d["product"].id,
            product_name=d["product"].name,
            qty_damaged=d["damage_item"].qty_damaged,
            cost_price=d["damage_item"].cost_price,
            loss_value=d["loss_value"],
            batch_number=d["damage_item"].batch_number,
            expiry_date=d["damage_item"].expiry_date
        )
        db.add(di)

        # Stock minus karo
        stock_before = d["product"].stock_qty
        d["product"].stock_qty -= d["damage_item"].qty_damaged

        movement = StockMovement(
            product_id=d["product"].id,
            movement_type="damage_out",
            qty=d["damage_item"].qty_damaged,
            stock_before=stock_before,
            stock_after=d["product"].stock_qty,
            reference=entry_number,
            notes=f"{data.damage_type} — {data.reason or ''}",
            created_by=current_user.username
        )
        db.add(movement)

        stock_updates.append({
            "product": d["product"].name,
            "qty_damaged": d["damage_item"].qty_damaged,
            "loss_value": d["loss_value"],
            "remaining_stock": d["product"].stock_qty
        })

    db.commit()
    db.refresh(entry)

    return {
        "message": f"Damage entry {entry_number} recorded",
        "entry_id": entry.id,
        "entry_number": entry_number,
        "damage_type": data.damage_type,
        "total_loss": entry.total_loss_value,
        "stock_updates": stock_updates
    }


# ──────────────────────────────────────
# 2. List Damage Entries
# ──────────────────────────────────────
@router.get("/")
def list_damage_entries(
    damage_type: Optional[str] = Query(None, description="damaged / expired / lost / stolen"),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Damage entries ki list"""
    query = db.query(DamageEntry)

    if damage_type:
        query = query.filter(DamageEntry.damage_type == damage_type)
    if from_date:
        query = query.filter(DamageEntry.entry_date >= from_date)
    if to_date:
        query = query.filter(DamageEntry.entry_date <= to_date)

    entries = query.order_by(DamageEntry.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for e in entries:
        result.append({
            "id": e.id,
            "entry_number": e.entry_number,
            "entry_date": e.entry_date,
            "damage_type": e.damage_type,
            "reason": e.reason,
            "total_loss_value": e.total_loss_value,
            "status": e.status,
            "recorded_by": e.recorded_by,
            "items_count": len(e.items)
        })

    return {"total": len(result), "entries": result}


# ──────────────────────────────────────
# 3. Damage Report (Summary by type & period)
# ──────────────────────────────────────
@router.get("/report")
def damage_report(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Damage & wastage summary report"""
    query = db.query(DamageEntry)

    if from_date:
        query = query.filter(DamageEntry.entry_date >= from_date)
    if to_date:
        query = query.filter(DamageEntry.entry_date <= to_date)

    entries = query.all()

    # Type-wise summary
    type_summary = {}
    product_summary = {}
    total_loss = 0.0

    for entry in entries:
        t = entry.damage_type
        if t not in type_summary:
            type_summary[t] = {"count": 0, "loss": 0.0}
        type_summary[t]["count"] += 1
        type_summary[t]["loss"] += entry.total_loss_value
        total_loss += entry.total_loss_value

        for item in entry.items:
            if item.product_name not in product_summary:
                product_summary[item.product_name] = {"qty": 0, "loss": 0.0}
            product_summary[item.product_name]["qty"] += item.qty_damaged
            product_summary[item.product_name]["loss"] += item.loss_value

    # Top 10 products by loss
    top_products = sorted(
        [{"product": k, "qty": v["qty"], "loss": round(v["loss"], 2)}
         for k, v in product_summary.items()],
        key=lambda x: x["loss"], reverse=True
    )[:10]

    return {
        "period": {"from": from_date, "to": to_date},
        "total_entries": len(entries),
        "total_loss_value": round(total_loss, 2),
        "by_type": {k: {"count": v["count"], "loss": round(v["loss"], 2)} for k, v in type_summary.items()},
        "top_damaged_products": top_products
    }

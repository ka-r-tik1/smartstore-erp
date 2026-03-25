# SmartStore ERP — Stock Transfer API
# Ek location se doosri location pe stock move karo
# Godown → Shop, Shop A → Shop B, Counter → Storage

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.product import Product
from app.models.stock_transfer import StockTransfer, StockTransferItem
from app.models.inventory import StockMovement
from app.models.user import User

router = APIRouter(prefix="/stock-transfer", tags=["Stock Transfer"])


# ─── Pydantic Schemas ───────────────────────────────────────


class TransferItemIn(BaseModel):
    product_id: int
    qty_requested: int
    unit_value: Optional[float] = 0.0


class StockTransferCreate(BaseModel):
    from_location: str      # Godown / Shop A / Counter
    to_location: str        # Shop B / Storage
    transfer_date: date
    items: List[TransferItemIn]
    notes: Optional[str] = None


class DispatchData(BaseModel):
    items: List[dict]       # [{transfer_item_id, qty_dispatched}]
    notes: Optional[str] = None


class ReceiveData(BaseModel):
    items: List[dict]       # [{transfer_item_id, qty_received}]
    notes: Optional[str] = None


# ─── Helper ─────────────────────────────────────────────────


def gen_transfer_number(db: Session) -> str:
    year = datetime.now().year
    prefix = f"ST-{year}-"
    last = db.query(StockTransfer).filter(
        StockTransfer.transfer_number.like(f"{prefix}%")
    ).order_by(StockTransfer.id.desc()).first()
    num = (int(last.transfer_number.split("-")[-1]) + 1) if last else 1
    return f"{prefix}{num:04d}"


# ──────────────────────────────────────
# 1. Create Stock Transfer Request
# ──────────────────────────────────────
@router.post("/", status_code=201)
def create_transfer(
    data: StockTransferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner", "staff"]))
):
    """Stock transfer request banao"""

    if data.from_location == data.to_location:
        raise HTTPException(status_code=400, detail="From aur To location same nahi ho sakti")

    transfer_number = gen_transfer_number(db)
    items_data = []
    total_value = 0.0

    for item in data.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product ID {item.product_id} nahi mila")

        if product.stock_qty < item.qty_requested:
            raise HTTPException(
                status_code=400,
                detail=f"{product.name}: stock {product.stock_qty}, request {item.qty_requested} nahi ho sakta"
            )

        unit_val = item.unit_value or product.purchase_price or 0.0
        items_data.append({
            "product": product,
            "transfer_item": item,
            "unit_value": unit_val,
            "item_value": round(unit_val * item.qty_requested, 2)
        })
        total_value += unit_val * item.qty_requested

    transfer = StockTransfer(
        transfer_number=transfer_number,
        from_location=data.from_location,
        to_location=data.to_location,
        transfer_date=data.transfer_date,
        status="pending",
        total_items=len(data.items),
        total_value=round(total_value, 2),
        requested_by=current_user.username,
        notes=data.notes
    )

    db.add(transfer)
    db.flush()

    for d in items_data:
        ti = StockTransferItem(
            transfer_id=transfer.id,
            product_id=d["product"].id,
            product_name=d["product"].name,
            qty_requested=d["transfer_item"].qty_requested,
            qty_dispatched=0,
            qty_received=0,
            unit_value=d["unit_value"],
            total_value=d["item_value"]
        )
        db.add(ti)

    db.commit()
    db.refresh(transfer)

    return {
        "message": f"Transfer {transfer_number} created",
        "transfer_id": transfer.id,
        "transfer_number": transfer_number,
        "from": data.from_location,
        "to": data.to_location,
        "total_value": transfer.total_value,
        "status": transfer.status
    }


# ──────────────────────────────────────
# 2. Dispatch Transfer (stock minus from source)
# ──────────────────────────────────────
@router.post("/{transfer_id}/dispatch")
def dispatch_transfer(
    transfer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner", "staff"]))
):
    """Transfer dispatch karo — source se stock minus"""
    transfer = db.query(StockTransfer).filter(StockTransfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer nahi mila")
    if transfer.status != "pending":
        raise HTTPException(status_code=400, detail=f"Transfer status '{transfer.status}' hai")

    dispatched = []
    for item in transfer.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            if product.stock_qty < item.qty_requested:
                raise HTTPException(
                    status_code=400,
                    detail=f"{product.name}: stock {product.stock_qty} hai, {item.qty_requested} dispatch nahi hoga"
                )
            stock_before = product.stock_qty
            product.stock_qty -= item.qty_requested
            item.qty_dispatched = item.qty_requested

            movement = StockMovement(
                product_id=product.id,
                movement_type="transfer_out",
                qty=item.qty_requested,
                stock_before=stock_before,
                stock_after=product.stock_qty,
                reference=transfer.transfer_number,
                notes=f"Transfer to {transfer.to_location}",
                created_by=current_user.username
            )
            db.add(movement)
            dispatched.append(f"{product.name}: -{item.qty_requested}")

    transfer.status = "in_transit"
    transfer.dispatched_by = current_user.username
    db.commit()

    return {
        "message": f"Transfer {transfer.transfer_number} dispatched",
        "status": "in_transit",
        "dispatched_items": dispatched
    }


# ──────────────────────────────────────
# 3. Receive Transfer (stock plus at destination)
# ──────────────────────────────────────
@router.post("/{transfer_id}/receive")
def receive_transfer(
    transfer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner", "staff"]))
):
    """Transfer receive karo — destination pe stock plus"""
    transfer = db.query(StockTransfer).filter(StockTransfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer nahi mila")
    if transfer.status != "in_transit":
        raise HTTPException(status_code=400, detail=f"Transfer '{transfer.status}' hai, pehle dispatch karo")

    received = []
    for item in transfer.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            stock_before = product.stock_qty
            product.stock_qty += item.qty_dispatched
            item.qty_received = item.qty_dispatched

            movement = StockMovement(
                product_id=product.id,
                movement_type="transfer_in",
                qty=item.qty_dispatched,
                stock_before=stock_before,
                stock_after=product.stock_qty,
                reference=transfer.transfer_number,
                notes=f"Transfer from {transfer.from_location}",
                created_by=current_user.username
            )
            db.add(movement)
            received.append(f"{product.name}: +{item.qty_dispatched}")

    transfer.status = "received"
    transfer.received_by = current_user.username
    transfer.received_date = date.today()
    db.commit()

    return {
        "message": f"Transfer {transfer.transfer_number} received",
        "status": "received",
        "received_items": received
    }


# ──────────────────────────────────────
# 4. List Transfers
# ──────────────────────────────────────
@router.get("/")
def list_transfers(
    status: Optional[str] = Query(None, description="pending / in_transit / received / cancelled"),
    from_location: Optional[str] = Query(None),
    to_location: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Stock transfers ki list"""
    query = db.query(StockTransfer)

    if status:
        query = query.filter(StockTransfer.status == status)
    if from_location:
        query = query.filter(StockTransfer.from_location == from_location)
    if to_location:
        query = query.filter(StockTransfer.to_location == to_location)

    transfers = query.order_by(StockTransfer.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for t in transfers:
        result.append({
            "id": t.id,
            "transfer_number": t.transfer_number,
            "from_location": t.from_location,
            "to_location": t.to_location,
            "transfer_date": t.transfer_date,
            "total_items": t.total_items,
            "total_value": t.total_value,
            "status": t.status,
            "requested_by": t.requested_by
        })

    return {"total": len(result), "transfers": result}

# SmartStore ERP — GRN (Goods Received Note) API
# Jab supplier se maal aata hai, GRN banate hain
# PO ke against actual goods check karo — qty, quality, batch, expiry

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.product import Product
from app.models.dealer import Dealer
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.grn import GRN, GRNItem
from app.models.inventory import StockMovement, StockBatch
from app.models.user import User

router = APIRouter(prefix="/grn", tags=["GRN - Goods Received Note"])


# ─── Pydantic Schemas ───────────────────────────────────────


class GRNItemIn(BaseModel):
    product_id: int
    qty_ordered: Optional[int] = 0
    qty_received: int
    qty_accepted: int
    qty_rejected: Optional[int] = 0
    unit_price: float
    batch_number: Optional[str] = None
    expiry_date: Optional[date] = None
    rejection_reason: Optional[str] = None


class GRNCreate(BaseModel):
    po_id: Optional[int] = None
    po_number: Optional[str] = None
    supplier_id: int
    received_date: date
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    vehicle_number: Optional[str] = None
    quality_check: Optional[bool] = False
    quality_notes: Optional[str] = None
    items: List[GRNItemIn]
    notes: Optional[str] = None


# ─── Helper ─────────────────────────────────────────────────


def gen_grn_number(db: Session) -> str:
    year = datetime.now().year
    prefix = f"GRN-{year}-"
    last = db.query(GRN).filter(
        GRN.grn_number.like(f"{prefix}%")
    ).order_by(GRN.id.desc()).first()
    num = (int(last.grn_number.split("-")[-1]) + 1) if last else 1
    return f"{prefix}{num:04d}"


# ──────────────────────────────────────
# 1. Create GRN (Draft)
# ──────────────────────────────────────
@router.post("/", status_code=201)
def create_grn(
    data: GRNCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner", "staff"]))
):
    """Naya GRN banao — supplier se maal aaya ka record"""

    supplier = db.query(Dealer).filter(Dealer.id == data.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier nahi mila")

    grn_number = gen_grn_number(db)
    items_data = []
    subtotal = 0.0
    total_gst = 0.0

    for item in data.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product ID {item.product_id} nahi mila")

        accepted_gst = round(item.unit_price * item.qty_accepted * product.gst_rate / 100, 2)
        item_total = round(item.unit_price * item.qty_accepted + accepted_gst, 2)

        items_data.append({
            "product": product,
            "grn_item": item,
            "gst_rate": product.gst_rate,
            "item_gst": accepted_gst,
            "item_total": item_total
        })
        subtotal += item.unit_price * item.qty_accepted
        total_gst += accepted_gst

    grn = GRN(
        grn_number=grn_number,
        po_id=data.po_id,
        po_number=data.po_number,
        supplier_id=data.supplier_id,
        received_date=data.received_date,
        invoice_number=data.invoice_number,
        invoice_date=data.invoice_date,
        vehicle_number=data.vehicle_number,
        status="draft",
        quality_check=data.quality_check,
        quality_notes=data.quality_notes,
        subtotal=round(subtotal, 2),
        gst_amount=round(total_gst, 2),
        grand_total=round(subtotal + total_gst, 2),
        received_by=current_user.username,
        notes=data.notes
    )

    db.add(grn)
    db.flush()

    for d in items_data:
        gi = GRNItem(
            grn_id=grn.id,
            product_id=d["product"].id,
            product_name=d["product"].name,
            qty_ordered=d["grn_item"].qty_ordered,
            qty_received=d["grn_item"].qty_received,
            qty_accepted=d["grn_item"].qty_accepted,
            qty_rejected=d["grn_item"].qty_rejected or 0,
            unit_price=d["grn_item"].unit_price,
            gst_rate=d["gst_rate"],
            gst_amount=d["item_gst"],
            total=d["item_total"],
            batch_number=d["grn_item"].batch_number,
            expiry_date=d["grn_item"].expiry_date,
            rejection_reason=d["grn_item"].rejection_reason
        )
        db.add(gi)

    db.commit()
    db.refresh(grn)

    return {
        "message": f"GRN {grn_number} created",
        "grn_id": grn.id,
        "grn_number": grn_number,
        "supplier": supplier.name,
        "grand_total": grn.grand_total,
        "status": grn.status
    }


# ──────────────────────────────────────
# 2. Verify GRN & Update Stock
# ──────────────────────────────────────
@router.post("/{grn_id}/verify")
def verify_grn(
    grn_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """GRN verify karo — accepted qty ka stock update hoga"""
    grn = db.query(GRN).filter(GRN.id == grn_id).first()
    if not grn:
        raise HTTPException(status_code=404, detail="GRN nahi mila")
    if grn.status != "draft":
        raise HTTPException(status_code=400, detail=f"GRN status '{grn.status}' hai, sirf draft verify hota hai")

    stock_updates = []

    for item in grn.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product and item.qty_accepted > 0:
            stock_before = product.stock_qty
            product.stock_qty += item.qty_accepted

            movement = StockMovement(
                product_id=product.id,
                movement_type="grn_in",
                qty=item.qty_accepted,
                stock_before=stock_before,
                stock_after=product.stock_qty,
                reference=grn.grn_number,
                notes=f"GRN verified — {grn.invoice_number or ''}",
                created_by=current_user.username
            )
            db.add(movement)

            # Batch create agar batch/expiry hai
            if item.batch_number or item.expiry_date:
                batch = StockBatch(
                    product_id=product.id,
                    batch_number=item.batch_number,
                    qty=item.qty_accepted,
                    purchase_price=item.unit_price,
                    expiry_date=item.expiry_date
                )
                db.add(batch)

            stock_updates.append({
                "product": product.name,
                "accepted": item.qty_accepted,
                "rejected": item.qty_rejected,
                "new_stock": product.stock_qty
            })

    grn.status = "stock_updated"
    grn.verified_by = current_user.username

    # PO update karo agar linked hai
    if grn.po_id:
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == grn.po_id).first()
        if po:
            for item in grn.items:
                po_item = db.query(PurchaseOrderItem).filter(
                    PurchaseOrderItem.po_id == po.id,
                    PurchaseOrderItem.product_id == item.product_id
                ).first()
                if po_item:
                    po_item.qty_received += item.qty_accepted

    db.commit()

    return {
        "message": f"GRN {grn.grn_number} verified — stock updated",
        "stock_updates": stock_updates
    }


# ──────────────────────────────────────
# 3. List GRNs
# ──────────────────────────────────────
@router.get("/")
def list_grns(
    status: Optional[str] = Query(None, description="draft / verified / stock_updated"),
    supplier_id: Optional[int] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """GRN list"""
    query = db.query(GRN)

    if status:
        query = query.filter(GRN.status == status)
    if supplier_id:
        query = query.filter(GRN.supplier_id == supplier_id)
    if from_date:
        query = query.filter(GRN.received_date >= from_date)
    if to_date:
        query = query.filter(GRN.received_date <= to_date)

    grns = query.order_by(GRN.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for g in grns:
        supplier = db.query(Dealer).filter(Dealer.id == g.supplier_id).first()
        result.append({
            "id": g.id,
            "grn_number": g.grn_number,
            "po_number": g.po_number,
            "supplier": supplier.name if supplier else "Unknown",
            "received_date": g.received_date,
            "invoice_number": g.invoice_number,
            "grand_total": g.grand_total,
            "quality_check": g.quality_check,
            "status": g.status,
            "items_count": len(g.items)
        })

    return {"total": len(result), "grns": result}


# ──────────────────────────────────────
# 4. GRN Detail
# ──────────────────────────────────────
@router.get("/{grn_id}")
def get_grn(
    grn_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """GRN full detail"""
    grn = db.query(GRN).filter(GRN.id == grn_id).first()
    if not grn:
        raise HTTPException(status_code=404, detail="GRN nahi mila")

    supplier = db.query(Dealer).filter(Dealer.id == grn.supplier_id).first()

    return {
        "id": grn.id,
        "grn_number": grn.grn_number,
        "po_number": grn.po_number,
        "supplier": supplier.name if supplier else "Unknown",
        "received_date": grn.received_date,
        "invoice_number": grn.invoice_number,
        "invoice_date": grn.invoice_date,
        "vehicle_number": grn.vehicle_number,
        "quality_check": grn.quality_check,
        "quality_notes": grn.quality_notes,
        "subtotal": grn.subtotal,
        "gst_amount": grn.gst_amount,
        "grand_total": grn.grand_total,
        "status": grn.status,
        "received_by": grn.received_by,
        "verified_by": grn.verified_by,
        "items": [
            {
                "product_name": i.product_name,
                "qty_ordered": i.qty_ordered,
                "qty_received": i.qty_received,
                "qty_accepted": i.qty_accepted,
                "qty_rejected": i.qty_rejected,
                "unit_price": i.unit_price,
                "batch_number": i.batch_number,
                "expiry_date": i.expiry_date,
                "rejection_reason": i.rejection_reason,
                "total": i.total
            }
            for i in grn.items
        ]
    }

# SmartStore ERP — Purchase Orders API
# PO banao, approve karo, maal receive karo, stock auto-update

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.product import Product
from app.models.dealer import Dealer
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.inventory import StockMovement, StockBatch
from app.models.user import User
from app.schemas.purchase import POCreate, POReceive, POResponse

router = APIRouter(prefix="/purchase", tags=["Purchase Orders"])


def generate_po_number(db: Session) -> str:
    """PO number generate — PO-2026-0001 format"""
    year = datetime.now().year
    prefix = f"PO-{year}-"
    last_po = db.query(PurchaseOrder).filter(
        PurchaseOrder.po_number.like(f"{prefix}%")
    ).order_by(PurchaseOrder.id.desc()).first()

    if last_po:
        last_num = int(last_po.po_number.split("-")[-1])
        new_num = last_num + 1
    else:
        new_num = 1
    return f"{prefix}{new_num:04d}"


# ──────────────────────────────────────
# 1. Create Purchase Order (Draft)
# ──────────────────────────────────────
@router.post("/", response_model=POResponse, status_code=201)
def create_po(
    data: POCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner", "staff"]))
):
    """Naya Purchase Order banao (draft state mein)"""

    # Supplier check
    supplier = db.query(Dealer).filter(Dealer.id == data.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier nahi mila")
    if supplier.dealer_type not in ["supplier", "both"]:
        raise HTTPException(status_code=400, detail=f"{supplier.name} supplier nahi hai")

    po_number = generate_po_number(db)
    po_items = []
    subtotal = 0.0
    total_gst = 0.0

    for item in data.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product ID {item.product_id} nahi mila")

        item_subtotal = item.unit_price * item.qty_ordered
        item_gst = round(item_subtotal * product.gst_rate / 100, 2)
        item_total = round(item_subtotal + item_gst, 2)

        po_item = PurchaseOrderItem(
            product_id=product.id,
            product_name=product.name,
            qty_ordered=item.qty_ordered,
            unit_price=item.unit_price,
            gst_rate=product.gst_rate,
            gst_amount=item_gst,
            total=item_total
        )
        po_items.append(po_item)
        subtotal += item_subtotal
        total_gst += item_gst

    po = PurchaseOrder(
        po_number=po_number,
        supplier_id=data.supplier_id,
        status="draft",
        subtotal=round(subtotal, 2),
        gst_amount=round(total_gst, 2),
        grand_total=round(subtotal + total_gst, 2),
        expected_date=data.expected_date,
        notes=data.notes,
        created_by=current_user.username
    )

    db.add(po)
    db.flush()

    for item in po_items:
        item.po_id = po.id
        db.add(item)

    db.commit()
    db.refresh(po)
    return po


# ──────────────────────────────────────
# 2. List Purchase Orders
# ──────────────────────────────────────
@router.get("/", response_model=list[POResponse])
def list_pos(
    status: Optional[str] = Query(None, description="draft / approved / received / cancelled"),
    supplier_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Purchase Orders ki list"""
    query = db.query(PurchaseOrder)

    if status:
        query = query.filter(PurchaseOrder.status == status)
    if supplier_id:
        query = query.filter(PurchaseOrder.supplier_id == supplier_id)

    pos = query.order_by(PurchaseOrder.created_at.desc()).offset(skip).limit(limit).all()
    return pos


# ──────────────────────────────────────
# 3. PO Detail
# ──────────────────────────────────────
@router.get("/{po_id}", response_model=POResponse)
def get_po(
    po_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Purchase Order ki full detail"""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="PO nahi mila")
    return po


# ──────────────────────────────────────
# 4. Approve PO (Owner only)
# ──────────────────────────────────────
@router.post("/{po_id}/approve")
def approve_po(
    po_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """PO approve karo — sirf Owner"""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="PO nahi mila")
    if po.status != "draft":
        raise HTTPException(status_code=400, detail=f"PO status '{po.status}' hai, sirf draft approve hota hai")

    po.status = "approved"
    po.approved_by = current_user.username
    db.commit()

    return {"message": f"PO {po.po_number} approved by {current_user.username}"}


# ──────────────────────────────────────
# 5. Receive Goods (stock auto-update + batch create)
# ──────────────────────────────────────
@router.post("/{po_id}/receive")
def receive_goods(
    po_id: int,
    data: POReceive,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner", "staff"]))
):
    """Maal receive karo — stock + batch auto-update"""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="PO nahi mila")
    if po.status not in ["approved", "received"]:
        raise HTTPException(status_code=400, detail=f"PO status '{po.status}' hai. Pehle approve karo")

    received_items = []

    for recv_item in data.items:
        po_item = db.query(PurchaseOrderItem).filter(
            PurchaseOrderItem.id == recv_item.po_item_id,
            PurchaseOrderItem.po_id == po_id
        ).first()
        if not po_item:
            raise HTTPException(status_code=404, detail=f"PO Item ID {recv_item.po_item_id} nahi mila")

        remaining = po_item.qty_ordered - po_item.qty_received
        if recv_item.qty_received > remaining:
            raise HTTPException(
                status_code=400,
                detail=f"{po_item.product_name}: sirf {remaining} baaki, {recv_item.qty_received} nahi le sakte"
            )

        # PO item update
        po_item.qty_received += recv_item.qty_received

        # Product stock update
        product = db.query(Product).filter(Product.id == po_item.product_id).first()
        if product:
            stock_before = product.stock_qty
            product.stock_qty += recv_item.qty_received

            # Stock movement log
            movement = StockMovement(
                product_id=product.id,
                movement_type="purchase_in",
                qty=recv_item.qty_received,
                stock_before=stock_before,
                stock_after=product.stock_qty,
                reference=po.po_number,
                notes=data.notes,
                created_by=current_user.username
            )
            db.add(movement)

            # Batch create (agar batch/expiry di hai)
            if recv_item.batch_number or recv_item.expiry_date:
                batch = StockBatch(
                    product_id=product.id,
                    batch_number=recv_item.batch_number,
                    qty=recv_item.qty_received,
                    purchase_price=po_item.unit_price,
                    expiry_date=recv_item.expiry_date
                )
                db.add(batch)

        received_items.append({
            "product": po_item.product_name,
            "received": recv_item.qty_received,
            "total_received": po_item.qty_received,
            "ordered": po_item.qty_ordered
        })

    # Check if all items fully received
    all_received = all(
        item.qty_received >= item.qty_ordered
        for item in po.items
    )

    po.status = "received" if all_received else "approved"
    if all_received:
        po.received_date = date.today()

    db.commit()

    return {
        "message": f"Goods received for {po.po_number}",
        "status": po.status,
        "items": received_items
    }


# ──────────────────────────────────────
# 6. Cancel PO (Owner only)
# ──────────────────────────────────────
@router.post("/{po_id}/cancel")
def cancel_po(
    po_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """PO cancel karo"""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="PO nahi mila")
    if po.status == "received":
        raise HTTPException(status_code=400, detail="Received PO cancel nahi hota")

    po.status = "cancelled"
    db.commit()

    return {"message": f"PO {po.po_number} cancelled"}

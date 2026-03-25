# SmartStore ERP — Returns API
# Sales Return: Customer ne product wapas kiya — stock wapas, refund
# Purchase Return: Supplier ko maal wapas — debit note, stock minus

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.product import Product
from app.models.dealer import Dealer
from app.models.order import Order
from app.models.purchase import PurchaseOrder
from app.models.returns import SalesReturn, SalesReturnItem, PurchaseReturn, PurchaseReturnItem
from app.models.inventory import StockMovement
from app.models.user import User

router = APIRouter(prefix="/returns", tags=["Returns"])


# ─── Pydantic Schemas ───────────────────────────────────────


class ReturnItemIn(BaseModel):
    product_id: int
    qty_returned: int
    unit_price: float
    condition: Optional[str] = "good"  # good / damaged / expired


class SalesReturnCreate(BaseModel):
    original_invoice: Optional[str] = None
    order_id: Optional[int] = None
    dealer_id: Optional[int] = None
    return_date: date
    reason: Optional[str] = None
    refund_mode: Optional[str] = "cash"   # cash / credit_note / upi
    items: List[ReturnItemIn]
    notes: Optional[str] = None


class PurchaseReturnItemIn(BaseModel):
    product_id: int
    qty_returned: int
    unit_price: float


class PurchaseReturnCreate(BaseModel):
    original_po: Optional[str] = None
    po_id: Optional[int] = None
    supplier_id: int
    return_date: date
    reason: Optional[str] = None
    items: List[PurchaseReturnItemIn]
    notes: Optional[str] = None


# ─── Helper: Number Generators ──────────────────────────────


def gen_sales_return_number(db: Session) -> str:
    year = datetime.now().year
    prefix = f"SR-{year}-"
    last = db.query(SalesReturn).filter(
        SalesReturn.return_number.like(f"{prefix}%")
    ).order_by(SalesReturn.id.desc()).first()
    num = (int(last.return_number.split("-")[-1]) + 1) if last else 1
    return f"{prefix}{num:04d}"


def gen_purchase_return_number(db: Session) -> str:
    year = datetime.now().year
    prefix = f"PR-{year}-"
    last = db.query(PurchaseReturn).filter(
        PurchaseReturn.return_number.like(f"{prefix}%")
    ).order_by(PurchaseReturn.id.desc()).first()
    num = (int(last.return_number.split("-")[-1]) + 1) if last else 1
    return f"{prefix}{num:04d}"


# ════════════════════════════════════════
# SALES RETURNS
# ════════════════════════════════════════


# ──────────────────────────────────────
# 1. Create Sales Return
# ──────────────────────────────────────
@router.post("/sales", status_code=201)
def create_sales_return(
    data: SalesReturnCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner", "staff"]))
):
    """Customer ka return banao — stock wapas + refund"""

    return_number = gen_sales_return_number(db)
    items_data = []
    subtotal = 0.0
    total_gst = 0.0

    for item in data.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product ID {item.product_id} nahi mila")

        item_gst = round(item.unit_price * item.qty_returned * product.gst_rate / 100, 2)
        item_total = round(item.unit_price * item.qty_returned + item_gst, 2)

        items_data.append({
            "product": product,
            "return_item": item,
            "gst_rate": product.gst_rate,
            "item_gst": item_gst,
            "item_total": item_total
        })
        subtotal += item.unit_price * item.qty_returned
        total_gst += item_gst

    sr = SalesReturn(
        return_number=return_number,
        original_invoice=data.original_invoice,
        order_id=data.order_id,
        dealer_id=data.dealer_id,
        return_date=data.return_date,
        reason=data.reason,
        status="pending",
        refund_mode=data.refund_mode,
        subtotal=round(subtotal, 2),
        gst_amount=round(total_gst, 2),
        total_refund=round(subtotal + total_gst, 2),
        notes=data.notes,
        processed_by=current_user.username
    )

    db.add(sr)
    db.flush()

    for d in items_data:
        sri = SalesReturnItem(
            return_id=sr.id,
            product_id=d["product"].id,
            product_name=d["product"].name,
            qty_returned=d["return_item"].qty_returned,
            unit_price=d["return_item"].unit_price,
            gst_rate=d["gst_rate"],
            gst_amount=d["item_gst"],
            total=d["item_total"],
            condition=d["return_item"].condition
        )
        db.add(sri)

    db.commit()
    db.refresh(sr)

    return {
        "message": f"Sales return {return_number} created",
        "return_id": sr.id,
        "return_number": return_number,
        "total_refund": sr.total_refund,
        "status": sr.status
    }


# ──────────────────────────────────────
# 2. Approve Sales Return (stock wapas + refund finalize)
# ──────────────────────────────────────
@router.post("/sales/{return_id}/approve")
def approve_sales_return(
    return_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """Return approve karo — stock wapas aayega"""
    sr = db.query(SalesReturn).filter(SalesReturn.id == return_id).first()
    if not sr:
        raise HTTPException(status_code=404, detail="Sales return nahi mila")
    if sr.status != "pending":
        raise HTTPException(status_code=400, detail=f"Return status '{sr.status}' hai, sirf pending approve hota hai")

    # Stock wapas karo (only good condition items)
    stock_updates = []
    for item in sr.items:
        if item.condition == "good":
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                stock_before = product.stock_qty
                product.stock_qty += item.qty_returned

                movement = StockMovement(
                    product_id=product.id,
                    movement_type="return_in",
                    qty=item.qty_returned,
                    stock_before=stock_before,
                    stock_after=product.stock_qty,
                    reference=sr.return_number,
                    notes=f"Sales return approved — {sr.reason or ''}",
                    created_by=current_user.username
                )
                db.add(movement)
                stock_updates.append(f"{product.name}: +{item.qty_returned}")

    sr.status = "refunded"
    db.commit()

    return {
        "message": f"Sales return {sr.return_number} approved & refunded",
        "refund_amount": sr.total_refund,
        "refund_mode": sr.refund_mode,
        "stock_restored": stock_updates
    }


# ──────────────────────────────────────
# 3. List Sales Returns
# ──────────────────────────────────────
@router.get("/sales")
def list_sales_returns(
    status: Optional[str] = Query(None, description="pending / refunded"),
    dealer_id: Optional[int] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sales returns ki list"""
    query = db.query(SalesReturn)

    if status:
        query = query.filter(SalesReturn.status == status)
    if dealer_id:
        query = query.filter(SalesReturn.dealer_id == dealer_id)
    if from_date:
        query = query.filter(SalesReturn.return_date >= from_date)
    if to_date:
        query = query.filter(SalesReturn.return_date <= to_date)

    returns = query.order_by(SalesReturn.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for r in returns:
        result.append({
            "id": r.id,
            "return_number": r.return_number,
            "original_invoice": r.original_invoice,
            "return_date": r.return_date,
            "reason": r.reason,
            "total_refund": r.total_refund,
            "refund_mode": r.refund_mode,
            "status": r.status,
            "items_count": len(r.items)
        })

    return {"total": len(result), "returns": result}


# ──────────────────────────────────────
# 4. Sales Return Detail
# ──────────────────────────────────────
@router.get("/sales/{return_id}")
def get_sales_return(
    return_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sales return ki full detail"""
    sr = db.query(SalesReturn).filter(SalesReturn.id == return_id).first()
    if not sr:
        raise HTTPException(status_code=404, detail="Sales return nahi mila")

    return {
        "id": sr.id,
        "return_number": sr.return_number,
        "original_invoice": sr.original_invoice,
        "return_date": sr.return_date,
        "reason": sr.reason,
        "status": sr.status,
        "refund_mode": sr.refund_mode,
        "subtotal": sr.subtotal,
        "gst_amount": sr.gst_amount,
        "total_refund": sr.total_refund,
        "processed_by": sr.processed_by,
        "items": [
            {
                "product_name": i.product_name,
                "qty_returned": i.qty_returned,
                "unit_price": i.unit_price,
                "condition": i.condition,
                "total": i.total
            }
            for i in sr.items
        ]
    }


# ════════════════════════════════════════
# PURCHASE RETURNS
# ════════════════════════════════════════


# ──────────────────────────────────────
# 5. Create Purchase Return
# ──────────────────────────────────────
@router.post("/purchase", status_code=201)
def create_purchase_return(
    data: PurchaseReturnCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner", "staff"]))
):
    """Supplier ko maal wapas bhejo — debit note create"""

    supplier = db.query(Dealer).filter(Dealer.id == data.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier nahi mila")

    return_number = gen_purchase_return_number(db)
    items_data = []
    subtotal = 0.0
    total_gst = 0.0

    for item in data.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product ID {item.product_id} nahi mila")

        # Check stock available
        if product.stock_qty < item.qty_returned:
            raise HTTPException(
                status_code=400,
                detail=f"{product.name}: stock {product.stock_qty}, return {item.qty_returned} nahi ho sakta"
            )

        item_gst = round(item.unit_price * item.qty_returned * product.gst_rate / 100, 2)
        item_total = round(item.unit_price * item.qty_returned + item_gst, 2)

        items_data.append({
            "product": product,
            "return_item": item,
            "gst_rate": product.gst_rate,
            "item_gst": item_gst,
            "item_total": item_total
        })
        subtotal += item.unit_price * item.qty_returned
        total_gst += item_gst

    pr = PurchaseReturn(
        return_number=return_number,
        original_po=data.original_po,
        po_id=data.po_id,
        supplier_id=data.supplier_id,
        return_date=data.return_date,
        reason=data.reason,
        status="pending",
        subtotal=round(subtotal, 2),
        gst_amount=round(total_gst, 2),
        total_amount=round(subtotal + total_gst, 2),
        notes=data.notes,
        created_by=current_user.username
    )

    db.add(pr)
    db.flush()

    for d in items_data:
        pri = PurchaseReturnItem(
            return_id=pr.id,
            product_id=d["product"].id,
            product_name=d["product"].name,
            qty_returned=d["return_item"].qty_returned,
            unit_price=d["return_item"].unit_price,
            gst_rate=d["gst_rate"],
            gst_amount=d["item_gst"],
            total=d["item_total"]
        )
        db.add(pri)

    db.commit()
    db.refresh(pr)

    return {
        "message": f"Purchase return {return_number} created",
        "return_id": pr.id,
        "return_number": return_number,
        "total_amount": pr.total_amount,
        "supplier": supplier.name,
        "status": pr.status
    }


# ──────────────────────────────────────
# 6. Send Purchase Return (stock minus + debit note)
# ──────────────────────────────────────
@router.post("/purchase/{return_id}/send")
def send_purchase_return(
    return_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """Purchase return approve karo — stock minus + debit note"""
    pr = db.query(PurchaseReturn).filter(PurchaseReturn.id == return_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="Purchase return nahi mila")
    if pr.status != "pending":
        raise HTTPException(status_code=400, detail=f"Return status '{pr.status}' hai")

    # Stock minus karo
    stock_updates = []
    for item in pr.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            if product.stock_qty < item.qty_returned:
                raise HTTPException(
                    status_code=400,
                    detail=f"{product.name}: stock sirf {product.stock_qty} hai"
                )
            stock_before = product.stock_qty
            product.stock_qty -= item.qty_returned

            movement = StockMovement(
                product_id=product.id,
                movement_type="return_out",
                qty=item.qty_returned,
                stock_before=stock_before,
                stock_after=product.stock_qty,
                reference=pr.return_number,
                notes=f"Purchase return to supplier — {pr.reason or ''}",
                created_by=current_user.username
            )
            db.add(movement)
            stock_updates.append(f"{product.name}: -{item.qty_returned}")

    # Debit note number generate
    pr.debit_note_number = f"DN-{pr.return_number}"
    pr.status = "debit_note"
    db.commit()

    return {
        "message": f"Purchase return {pr.return_number} sent to supplier",
        "debit_note": pr.debit_note_number,
        "total_debit": pr.total_amount,
        "stock_reduced": stock_updates
    }


# ──────────────────────────────────────
# 7. List Purchase Returns
# ──────────────────────────────────────
@router.get("/purchase")
def list_purchase_returns(
    status: Optional[str] = Query(None),
    supplier_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Purchase returns ki list"""
    query = db.query(PurchaseReturn)

    if status:
        query = query.filter(PurchaseReturn.status == status)
    if supplier_id:
        query = query.filter(PurchaseReturn.supplier_id == supplier_id)

    returns = query.order_by(PurchaseReturn.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for r in returns:
        supplier = db.query(Dealer).filter(Dealer.id == r.supplier_id).first()
        result.append({
            "id": r.id,
            "return_number": r.return_number,
            "supplier": supplier.name if supplier else "Unknown",
            "return_date": r.return_date,
            "total_amount": r.total_amount,
            "debit_note_number": r.debit_note_number,
            "status": r.status
        })

    return {"total": len(result), "returns": result}

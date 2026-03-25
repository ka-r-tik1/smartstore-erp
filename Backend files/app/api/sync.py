# SmartStore ERP — Offline Sync API

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.inventory import StockMovement
from app.models.user import User

router = APIRouter(prefix="/sync", tags=["Offline Sync"])


class OfflineBillItem(BaseModel):
    product_id: int
    qty: int
    unit_price: float


class OfflineBill(BaseModel):
    local_id: int
    order_type: str = "sale"
    payment_mode: str = "cash"
    payment_status: str = "paid"
    dealer_id: Optional[int] = None
    items: List[OfflineBillItem]
    offline_created_at: Optional[str] = None


def gen_invoice(db: Session) -> str:
    year = datetime.now().year
    prefix = f"INV-{year}-"
    last = db.query(Order).filter(Order.invoice_number.like(f"{prefix}%")).order_by(Order.id.desc()).first()
    num = (int(last.invoice_number.split("-")[-1]) + 1) if last else 1
    return f"{prefix}{num:04d}"


@router.post("/offline-bill")
def sync_offline_bill(
    data: OfflineBill,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Offline bill ko server pe process karo"""
    invoice_number = gen_invoice(db)
    items_data = []
    subtotal = 0.0
    total_gst = 0.0

    for item in data.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product ID {item.product_id} nahi mila")
        if product.stock_qty < item.qty:
            raise HTTPException(status_code=400, detail=f"{product.name}: stock {product.stock_qty} hai")

        base = item.unit_price * item.qty
        gst = round(base * product.gst_rate / 100, 2)
        items_data.append({"product": product, "qty": item.qty, "unit_price": item.unit_price, "gst_rate": product.gst_rate, "gst_amount": gst, "total": round(base + gst, 2)})
        subtotal += base
        total_gst += gst

    order = Order(
        invoice_number=invoice_number, dealer_id=data.dealer_id, order_type=data.order_type,
        subtotal=round(subtotal, 2), gst_amount=round(total_gst, 2), discount=0.0,
        grand_total=round(subtotal + total_gst, 2), payment_mode=data.payment_mode,
        payment_status=data.payment_status,
        notes=f"Offline sync (local_id:{data.local_id}, time:{data.offline_created_at})"
    )
    db.add(order)
    db.flush()

    for d in items_data:
        db.add(OrderItem(order_id=order.id, product_id=d["product"].id, product_name=d["product"].name, qty=d["qty"], unit_price=d["unit_price"], gst_rate=d["gst_rate"], gst_amount=d["gst_amount"], total=d["total"]))
        stock_before = d["product"].stock_qty
        d["product"].stock_qty -= d["qty"]
        db.add(StockMovement(product_id=d["product"].id, movement_type="sale_out", qty=d["qty"], stock_before=stock_before, stock_after=d["product"].stock_qty, reference=invoice_number, notes="Offline sync", created_by=current_user.username))

    db.commit()
    return {"message": "Synced", "local_id": data.local_id, "invoice_number": invoice_number, "grand_total": order.grand_total}


@router.get("/status")
def sync_status(current_user: User = Depends(get_current_user)):
    return {"status": "online", "server_time": datetime.now().isoformat(), "user": current_user.username}

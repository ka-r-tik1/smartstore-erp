# SmartStore ERP — Orders API
# All orders list, filter, detail, cancel/return

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime, date

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.dealer import Dealer
from app.models.user import User
from app.schemas.order import OrderResponse

router = APIRouter(prefix="/orders", tags=["Orders"])


# ──────────────────────────────────────
# 1. All Orders list (sales + purchases + returns)
# ──────────────────────────────────────
@router.get("/", response_model=list[OrderResponse])
def list_orders(
    order_type: Optional[str] = Query(None, description="sale / purchase / return"),
    payment_mode: Optional[str] = Query(None, description="cash / upi / card / udhaar"),
    payment_status: Optional[str] = Query(None, description="paid / pending / partial"),
    date_from: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    dealer_id: Optional[int] = Query(None, description="Dealer ID se filter"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Saare orders — filter by type, date, payment, dealer"""

    query = db.query(Order)

    if order_type:
        query = query.filter(Order.order_type == order_type)
    if payment_mode:
        query = query.filter(Order.payment_mode == payment_mode)
    if payment_status:
        query = query.filter(Order.payment_status == payment_status)
    if date_from:
        query = query.filter(func.date(Order.created_at) >= date_from)
    if date_to:
        query = query.filter(func.date(Order.created_at) <= date_to)
    if dealer_id:
        query = query.filter(Order.dealer_id == dealer_id)

    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    return orders


# ──────────────────────────────────────
# 2. Order detail by ID
# ──────────────────────────────────────
@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Order ki full detail with items"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order nahi mila")
    return order


# ──────────────────────────────────────
# 3. Order search by invoice number
# ──────────────────────────────────────
@router.get("/search/{invoice_number}", response_model=OrderResponse)
def search_order(
    invoice_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Invoice number se order dhundho"""
    order = db.query(Order).filter(Order.invoice_number == invoice_number).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Invoice '{invoice_number}' nahi mila")
    return order


# ──────────────────────────────────────
# 4. Cancel order (Owner only)
# ──────────────────────────────────────
@router.post("/{order_id}/cancel")
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """Order cancel karo — stock wapas aayega, dealer outstanding minus hoga"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order nahi mila")

    if order.order_type == "return":
        raise HTTPException(status_code=400, detail="Return order cancel nahi hota")

    # Stock wapas karo
    for item in order.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            product.stock_qty += item.qty

    # Dealer outstanding minus karo (agar udhaar tha)
    if order.payment_mode == "udhaar" and order.dealer_id:
        dealer = db.query(Dealer).filter(Dealer.id == order.dealer_id).first()
        if dealer:
            dealer.outstanding = max(0, dealer.outstanding - order.grand_total)

    order.order_type = "cancelled"
    order.payment_status = "cancelled"
    db.commit()

    return {"message": f"Order {order.invoice_number} cancelled. Stock restored."}


# ──────────────────────────────────────
# 5. Orders Summary (date range)
# ──────────────────────────────────────
@router.get("/summary/report")
def orders_summary(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """Orders ka summary — total sales, avg bill, payment breakup"""

    query = db.query(Order).filter(Order.order_type == "sale")

    if date_from:
        query = query.filter(func.date(Order.created_at) >= date_from)
    if date_to:
        query = query.filter(func.date(Order.created_at) <= date_to)

    orders = query.all()
    total_orders = len(orders)

    if total_orders == 0:
        return {"message": "No orders found", "total_orders": 0}

    total_revenue = sum(o.grand_total for o in orders)
    total_gst = sum(o.gst_amount for o in orders)
    total_discount = sum(o.discount for o in orders)
    avg_bill = total_revenue / total_orders

    cash = sum(o.grand_total for o in orders if o.payment_mode == "cash")
    upi = sum(o.grand_total for o in orders if o.payment_mode == "upi")
    card = sum(o.grand_total for o in orders if o.payment_mode == "card")
    udhaar = sum(o.grand_total for o in orders if o.payment_mode == "udhaar")

    return {
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "total_gst_collected": round(total_gst, 2),
        "total_discount_given": round(total_discount, 2),
        "avg_bill_value": round(avg_bill, 2),
        "payment_breakup": {
            "cash": round(cash, 2),
            "upi": round(upi, 2),
            "card": round(card, 2),
            "udhaar": round(udhaar, 2)
        }
    }

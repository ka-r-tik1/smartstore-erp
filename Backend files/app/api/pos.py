# SmartStore ERP — POS (Point of Sale) Billing API
# Cart se bill banao, invoice generate karo, stock auto-update, scheme auto-apply

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date
import pytz
IST = pytz.timezone('Asia/Kolkata')
from typing import Optional

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.dealer import Dealer
from app.models.scheme import Scheme
from app.models.user import User
from app.schemas.order import POSBillCreate, OrderResponse

router = APIRouter(prefix="/pos", tags=["POS - Billing"])


def generate_invoice_number(db: Session) -> str:
    """Invoice number generate karo — INV-2026-0001 format"""
    year = datetime.now().year
    prefix = f"INV-{year}-"

    # Last invoice number nikalo
    last_order = db.query(Order).filter(
        Order.invoice_number.like(f"{prefix}%")
    ).order_by(Order.id.desc()).first()

    if last_order:
        last_num = int(last_order.invoice_number.split("-")[-1])
        new_num = last_num + 1
    else:
        new_num = 1

    return f"{prefix}{new_num:04d}"


# ──────────────────────────────────────
# 1. Bill banao (Create Sale)
# ──────────────────────────────────────
@router.post("/bill", response_model=OrderResponse, status_code=201)
def create_bill(
    bill: POSBillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """POS se bill banao — cart items bhejo, invoice ban jayega, stock auto-update"""

    invoice_number = generate_invoice_number(db)
    order_items = []
    subtotal = 0.0
    total_gst = 0.0
    scheme_discount = 0.0
    applied_schemes = []

    # Active schemes load karo (Phase 10)
    today = date.today()
    active_schemes = db.query(Scheme).filter(
        Scheme.is_active == True,
        Scheme.start_date <= today,
        Scheme.end_date >= today
    ).all()

    # Har cart item process karo
    for item in bill.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product ID {item.product_id} nahi mila")

        if not product.is_active:
            raise HTTPException(status_code=400, detail=f"Product '{product.name}' discontinued hai")

        if product.stock_qty < item.qty:
            raise HTTPException(
                status_code=400,
                detail=f"'{product.name}' ka stock sirf {product.stock_qty} hai, {item.qty} maanga"
            )

        # Calculate amounts — use batch_prices breakdown if sent (most accurate)
        unit_price = item.selling_price if item.selling_price else product.selling_price
        if item.batch_prices:
            item_subtotal = sum(bp.price * bp.qty for bp in item.batch_prices)
        else:
            item_subtotal = unit_price * item.qty

        # Scheme auto-apply — best discount dhundho (Phase 10)
        best_discount = 0.0
        best_scheme_name = None
        for scheme in active_schemes:
            matches = False
            if scheme.apply_on == "all":
                matches = True
            elif scheme.apply_on == "category" and product.category:
                matches = scheme.apply_value and scheme.apply_value.lower() == product.category.lower()
            elif scheme.apply_on == "brand" and product.brand:
                matches = scheme.apply_value and scheme.apply_value.lower() == product.brand.lower()
            elif scheme.apply_on == "product":
                matches = scheme.apply_value and str(product.id) in scheme.apply_value.split(",")

            if not matches:
                continue
            if scheme.min_qty > 0 and item.qty < scheme.min_qty:
                continue

            disc = 0.0
            if scheme.scheme_type == "percent_off":
                disc = round(item_subtotal * scheme.discount_percent / 100, 2)
            elif scheme.scheme_type == "flat_off":
                disc = min(scheme.discount_amount, item_subtotal)
            elif scheme.scheme_type == "buy_x_get_y" and item.qty >= scheme.buy_qty:
                sets = item.qty // scheme.buy_qty
                free_qty = sets * scheme.get_qty
                disc = round(free_qty * product.selling_price, 2)

            if disc > best_discount:
                best_discount = disc
                best_scheme_name = scheme.name

        scheme_discount += best_discount
        if best_scheme_name:
            applied_schemes.append({"product": product.name, "scheme": best_scheme_name, "discount": best_discount})

        item_gst = round(item_subtotal * product.gst_rate / 100, 2)
        item_total = round(item_subtotal + item_gst, 2)

        # Order item banao
        order_item = OrderItem(
            product_id=product.id,
            product_name=product.name,
            qty=item.qty,
            unit_price=unit_price,
            gst_rate=product.gst_rate,
            gst_amount=item_gst,
            total=item_total
        )
        order_items.append(order_item)

        # Stock minus karo
        product.stock_qty -= item.qty

        subtotal += item_subtotal
        total_gst += item_gst

    # Grand total calculate karo (manual discount + scheme discount)
    total_discount = bill.discount + scheme_discount
    grand_total = round(subtotal + total_gst - total_discount, 2)

    # Payment status
    payment_status = "pending" if bill.payment_mode == "udhaar" else "paid"

    # Udhaar pe dealer ka outstanding update karo
    if bill.payment_mode == "udhaar" and bill.dealer_id:
        dealer = db.query(Dealer).filter(Dealer.id == bill.dealer_id).first()
        if dealer:
            if dealer.credit_limit > 0 and (dealer.outstanding + grand_total) > dealer.credit_limit:
                raise HTTPException(
                    status_code=400,
                    detail=f"{dealer.name} ka credit limit Rs {dealer.credit_limit} hai. Current outstanding: Rs {dealer.outstanding}. Naya bill Rs {grand_total} se limit cross hoga."
                )
            dealer.outstanding += grand_total

    # Order banao
    order = Order(
        invoice_number=invoice_number,
        dealer_id=bill.dealer_id,
        order_type="sale",
        subtotal=round(subtotal, 2),
        gst_amount=round(total_gst, 2),
        discount=round(total_discount, 2),
        grand_total=grand_total,
        payment_mode=bill.payment_mode,
        payment_status=payment_status,
        notes=bill.notes
    )

    db.add(order)
    db.flush()  # ID generate karo

    # Items ko order se link karo
    for item in order_items:
        item.order_id = order.id
        db.add(item)

    db.commit()
    db.refresh(order)
    return order


# ──────────────────────────────────────
# 2. Saare Bills list karo (with filters)
# ──────────────────────────────────────
@router.get("/bills", response_model=list[OrderResponse])
def list_bills(
    payment_mode: Optional[str] = Query(None, description="cash / upi / card / udhaar"),
    payment_status: Optional[str] = Query(None, description="paid / pending / partial"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Saare bills ki list — filter by payment mode/status"""

    query = db.query(Order).filter(Order.order_type == "sale")

    if payment_mode:
        query = query.filter(Order.payment_mode == payment_mode)
    if payment_status:
        query = query.filter(Order.payment_status == payment_status)

    bills = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    return bills


# ──────────────────────────────────────
# 3. Ek Bill ki detail (by ID)
# ──────────────────────────────────────
@router.get("/bills/{bill_id}", response_model=OrderResponse)
def get_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ek bill ki full detail with items"""
    bill = db.query(Order).filter(Order.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill nahi mila")
    return bill


# ──────────────────────────────────────
# 4. Aaj ki sale summary
# ──────────────────────────────────────
@router.get("/today-summary")
def today_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aaj ki total sale, bills count, payment mode wise breakup"""

    now_ist = datetime.now(IST)
    today = now_ist.date()
    # IST today ka UTC range (IST = UTC+5:30)
    from datetime import timedelta
    ist_start = datetime(today.year, today.month, today.day, 0, 0, 0) - timedelta(hours=5, minutes=30)
    ist_end = datetime(today.year, today.month, today.day, 23, 59, 59) - timedelta(hours=5, minutes=30)

    # Today's orders
    today_orders = db.query(Order).filter(
        Order.created_at >= ist_start,
        Order.created_at <= ist_end,
        Order.order_type == "sale"
    ).all()

    total_sale = sum(o.grand_total for o in today_orders)
    total_bills = len(today_orders)

    # Payment mode wise breakup
    cash_total = sum(o.grand_total for o in today_orders if o.payment_mode == "cash")
    upi_total = sum(o.grand_total for o in today_orders if o.payment_mode == "upi")
    card_total = sum(o.grand_total for o in today_orders if o.payment_mode == "card")
    udhaar_total = sum(o.grand_total for o in today_orders if o.payment_mode == "udhaar")

    return {
        "date": str(today),
        "total_bills": total_bills,
        "total_sale": round(total_sale, 2),
        "cash": round(cash_total, 2),
        "upi": round(upi_total, 2),
        "card": round(card_total, 2),
        "udhaar": round(udhaar_total, 2)
    }

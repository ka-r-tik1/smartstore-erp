# SmartStore ERP — Smart Alerts API
# Low stock, expiry warning, udhaar due, reorder alerts
# Owner ko important business signals milein

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, timedelta

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.product import Product
from app.models.inventory import StockBatch
from app.models.dealer import Dealer
from app.models.order import Order
from app.models.purchase import PurchaseOrder
from app.models.user import User

router = APIRouter(prefix="/alerts", tags=["Smart Alerts"])


# ──────────────────────────────────────
# 1. Low Stock Alerts
# ──────────────────────────────────────
@router.get("/low-stock")
def low_stock_alerts(
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Products jinka stock reorder level se neeche hai"""
    query = db.query(Product).filter(
        Product.is_active == True,
        Product.stock_qty <= Product.reorder_level
    )

    if category:
        query = query.filter(Product.category == category)

    products = query.order_by(Product.stock_qty.asc()).all()

    out_of_stock = []
    critical = []    # 0 se reorder level ka 25%
    low = []         # 25% se reorder level

    for p in products:
        item = {
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "brand": p.brand,
            "current_stock": p.stock_qty,
            "reorder_level": p.reorder_level,
            "unit": p.unit
        }
        if p.stock_qty <= 0:
            out_of_stock.append(item)
        elif p.stock_qty <= p.reorder_level * 0.25:
            critical.append(item)
        else:
            low.append(item)

    return {
        "summary": {
            "out_of_stock": len(out_of_stock),
            "critical": len(critical),
            "low_stock": len(low),
            "total_alerts": len(products)
        },
        "out_of_stock": out_of_stock,
        "critical_stock": critical,
        "low_stock": low
    }


# ──────────────────────────────────────
# 2. Expiry Alerts
# ──────────────────────────────────────
@router.get("/expiry")
def expiry_alerts(
    days_ahead: int = Query(30, ge=1, le=180, description="Kitne din mein expire honge"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Products jo agle X dino mein expire ho rahe hain"""
    today = date.today()
    warning_date = today + timedelta(days=days_ahead)

    batches = db.query(StockBatch).filter(
        StockBatch.expiry_date != None,
        StockBatch.expiry_date <= warning_date,
        StockBatch.qty > 0
    ).order_by(StockBatch.expiry_date.asc()).all()

    expired = []
    expiring_soon = []
    expiring_later = []

    for batch in batches:
        product = db.query(Product).filter(Product.id == batch.product_id).first()
        item = {
            "product_id": batch.product_id,
            "product_name": product.name if product else "Unknown",
            "category": product.category if product else "",
            "batch_number": batch.batch_number,
            "qty": batch.qty,
            "expiry_date": batch.expiry_date,
            "days_remaining": (batch.expiry_date - today).days
        }

        if batch.expiry_date < today:
            item["status"] = "EXPIRED"
            expired.append(item)
        elif batch.expiry_date <= today + timedelta(days=7):
            item["status"] = "EXPIRING THIS WEEK"
            expiring_soon.append(item)
        else:
            item["status"] = f"Expires in {item['days_remaining']} days"
            expiring_later.append(item)

    return {
        "check_date": today,
        "warning_window_days": days_ahead,
        "summary": {
            "already_expired": len(expired),
            "expiring_this_week": len(expiring_soon),
            "expiring_soon": len(expiring_later),
            "total_batches": len(batches)
        },
        "already_expired": expired,
        "expiring_this_week": expiring_soon,
        "expiring_within_days": expiring_later
    }


# ──────────────────────────────────────
# 3. Payment Due Alerts (Udhaar)
# ──────────────────────────────────────
@router.get("/payment-due")
def payment_due_alerts(
    min_amount: float = Query(0, ge=0, description="Minimum outstanding amount"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dealers jinhe payment karni hai ya jinse vasool karni hai"""
    dealers = db.query(Dealer).filter(
        Dealer.is_active == True,
        Dealer.outstanding > min_amount
    ).order_by(Dealer.outstanding.desc()).all()

    customers_pending = []   # Customer ne hamara paisa dena hai
    supplier_pending = []    # Hame supplier ko dena hai

    total_receivable = 0.0
    total_payable = 0.0

    for d in dealers:
        item = {
            "id": d.id,
            "name": d.name,
            "phone": d.phone,
            "outstanding": d.outstanding,
            "credit_limit": d.credit_limit,
            "dealer_type": d.dealer_type
        }
        if d.dealer_type in ["customer", "both"] and d.outstanding > 0:
            item["action"] = "COLLECT"
            customers_pending.append(item)
            total_receivable += d.outstanding
        elif d.dealer_type == "supplier" and d.outstanding > 0:
            item["action"] = "PAY"
            supplier_pending.append(item)
            total_payable += d.outstanding

    return {
        "summary": {
            "total_receivable": round(total_receivable, 2),
            "total_payable": round(total_payable, 2),
            "customers_with_due": len(customers_pending),
            "suppliers_with_due": len(supplier_pending)
        },
        "collect_from_customers": customers_pending,
        "pay_to_suppliers": supplier_pending
    }


# ──────────────────────────────────────
# 4. Dashboard Alerts (Sab kuch ek jagah)
# ──────────────────────────────────────
@router.get("/dashboard")
def dashboard_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Poori business ki important alerts — ek hi jagah"""
    today = date.today()

    # Low stock count
    low_stock_count = db.query(Product).filter(
        Product.is_active == True,
        Product.stock_qty <= Product.reorder_level
    ).count()

    out_of_stock_count = db.query(Product).filter(
        Product.is_active == True,
        Product.stock_qty <= 0
    ).count()

    # Expiry in 30 days
    expiry_30 = db.query(StockBatch).filter(
        StockBatch.expiry_date != None,
        StockBatch.expiry_date <= today + timedelta(days=30),
        StockBatch.qty > 0
    ).count()

    # Already expired
    expired_count = db.query(StockBatch).filter(
        StockBatch.expiry_date != None,
        StockBatch.expiry_date < today,
        StockBatch.qty > 0
    ).count()

    # Udhaar due
    udhaar_dealers = db.query(Dealer).filter(
        Dealer.outstanding > 0,
        Dealer.is_active == True
    ).all()
    total_receivable = sum(d.outstanding for d in udhaar_dealers if d.dealer_type in ["customer", "both"])
    total_payable = sum(d.outstanding for d in udhaar_dealers if d.dealer_type == "supplier")

    # Pending POs
    pending_pos = db.query(PurchaseOrder).filter(
        PurchaseOrder.status == "approved"
    ).count()

    # Today's sales
    today_orders = db.query(Order).filter(
        Order.created_at >= today,
        Order.order_type == "sale"
    ).all()
    today_revenue = sum(o.grand_total for o in today_orders)

    alerts = []

    if out_of_stock_count > 0:
        alerts.append({"type": "CRITICAL", "message": f"{out_of_stock_count} products OUT OF STOCK!", "action": "/api/alerts/low-stock"})
    if expired_count > 0:
        alerts.append({"type": "URGENT", "message": f"{expired_count} batches already EXPIRED", "action": "/api/alerts/expiry"})
    if low_stock_count > 0:
        alerts.append({"type": "WARNING", "message": f"{low_stock_count} products low stock", "action": "/api/alerts/low-stock"})
    if expiry_30 > 0:
        alerts.append({"type": "INFO", "message": f"{expiry_30} batches expiring in 30 days", "action": "/api/alerts/expiry"})
    if total_receivable > 0:
        alerts.append({"type": "INFO", "message": f"Rs {total_receivable:.0f} udhaar vasool karna hai", "action": "/api/alerts/payment-due"})
    if pending_pos > 0:
        alerts.append({"type": "INFO", "message": f"{pending_pos} Purchase Orders awaiting delivery", "action": "/api/purchase/?status=approved"})

    return {
        "date": today,
        "business_pulse": {
            "today_orders": len(today_orders),
            "today_revenue": round(today_revenue, 2),
            "total_receivable": round(total_receivable, 2),
            "total_payable": round(total_payable, 2)
        },
        "alert_counts": {
            "out_of_stock": out_of_stock_count,
            "low_stock": low_stock_count,
            "expiring_soon": expiry_30,
            "already_expired": expired_count,
            "pending_pos": pending_pos
        },
        "alerts": alerts
    }

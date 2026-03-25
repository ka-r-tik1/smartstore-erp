# SmartStore ERP — Data Hub API (Phase 12)
# Centralized Reports: Sales, Purchase, Profit/Loss, Tax, Daily/Monthly summaries
# Ek jagah pe poora business ka data

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, date
from typing import Optional
from collections import defaultdict

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.dealer import Dealer
from app.models.payment import Payment
from app.models.inventory import StockMovement, StockBatch
from app.models.staff import Staff, Payroll
from app.models.user import User

router = APIRouter(prefix="/data-hub", tags=["Data Hub - Reports"])


# ──────────────────────────────────────
# 1. Sales Report (date range)
# ──────────────────────────────────────
@router.get("/sales-report")
def sales_report(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    group_by: str = Query("daily", description="daily / weekly / monthly"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """Sales report — date range mein kitni sale hui, daily/weekly/monthly breakup"""

    orders = db.query(Order).filter(
        Order.order_type == "sale",
        func.date(Order.created_at) >= start_date,
        func.date(Order.created_at) <= end_date
    ).all()

    if not orders:
        return {"message": "Is period mein koi sale nahi hui", "data": []}

    # Group by period
    grouped = defaultdict(lambda: {"bills": 0, "subtotal": 0, "gst": 0, "discount": 0, "total": 0})

    for o in orders:
        if group_by == "daily":
            key = str(o.created_at.date())
        elif group_by == "weekly":
            week_start = o.created_at.date() - timedelta(days=o.created_at.weekday())
            key = f"Week {week_start}"
        else:  # monthly
            key = o.created_at.strftime("%Y-%m")

        grouped[key]["bills"] += 1
        grouped[key]["subtotal"] += o.subtotal
        grouped[key]["gst"] += o.gst_amount
        grouped[key]["discount"] += o.discount
        grouped[key]["total"] += o.grand_total

    report = []
    for period, data in sorted(grouped.items()):
        report.append({
            "period": period,
            "bills": data["bills"],
            "subtotal": round(data["subtotal"], 2),
            "gst": round(data["gst"], 2),
            "discount": round(data["discount"], 2),
            "total": round(data["total"], 2)
        })

    total_revenue = sum(o.grand_total for o in orders)
    total_gst = sum(o.gst_amount for o in orders)
    total_discount = sum(o.discount for o in orders)

    return {
        "start_date": str(start_date),
        "end_date": str(end_date),
        "group_by": group_by,
        "summary": {
            "total_bills": len(orders),
            "total_revenue": round(total_revenue, 2),
            "total_gst": round(total_gst, 2),
            "total_discount": round(total_discount, 2),
            "avg_bill_value": round(total_revenue / len(orders), 2)
        },
        "data": report
    }


# ──────────────────────────────────────
# 2. Purchase Report
# ──────────────────────────────────────
@router.get("/purchase-report")
def purchase_report(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """Purchase report — kitna maal khareeda, kis supplier se"""

    pos = db.query(PurchaseOrder).filter(
        func.date(PurchaseOrder.created_at) >= start_date,
        func.date(PurchaseOrder.created_at) <= end_date
    ).all()

    # Supplier-wise breakup
    supplier_wise = defaultdict(lambda: {"orders": 0, "total": 0})
    status_wise = defaultdict(int)

    for po in pos:
        supplier = db.query(Dealer).filter(Dealer.id == po.supplier_id).first()
        supplier_name = supplier.name if supplier else f"Supplier #{po.supplier_id}"
        supplier_wise[supplier_name]["orders"] += 1
        supplier_wise[supplier_name]["total"] += po.grand_total
        status_wise[po.status] += 1

    supplier_data = [
        {"supplier": name, "orders": data["orders"], "total": round(data["total"], 2)}
        for name, data in sorted(supplier_wise.items(), key=lambda x: x[1]["total"], reverse=True)
    ]

    total_purchase = sum(po.grand_total for po in pos)

    return {
        "start_date": str(start_date),
        "end_date": str(end_date),
        "summary": {
            "total_pos": len(pos),
            "total_purchase_value": round(total_purchase, 2),
            "status_breakup": dict(status_wise)
        },
        "supplier_wise": supplier_data
    }


# ──────────────────────────────────────
# 3. Profit & Loss Report
# ──────────────────────────────────────
@router.get("/profit-loss")
def profit_loss_report(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """Profit & Loss — revenue vs cost, gross/net profit"""

    # Revenue (sales)
    sales = db.query(Order).filter(
        Order.order_type == "sale",
        func.date(Order.created_at) >= start_date,
        func.date(Order.created_at) <= end_date
    ).all()

    total_revenue = sum(o.grand_total for o in sales)
    total_sales_gst = sum(o.gst_amount for o in sales)
    total_discount = sum(o.discount for o in sales)

    # COGS (Cost of Goods Sold) — from order items
    order_ids = [o.id for o in sales]
    if order_ids:
        items = db.query(OrderItem).filter(OrderItem.order_id.in_(order_ids)).all()
        cogs = 0.0
        for item in items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product and product.purchase_price:
                cogs += product.purchase_price * item.qty
            else:
                cogs += item.unit_price * 0.7 * item.qty  # Estimate 70% if no purchase price
    else:
        cogs = 0.0

    # Purchases
    purchases = db.query(PurchaseOrder).filter(
        PurchaseOrder.status == "received",
        func.date(PurchaseOrder.created_at) >= start_date,
        func.date(PurchaseOrder.created_at) <= end_date
    ).all()
    total_purchases = sum(po.grand_total for po in purchases)

    # Payroll expenses
    payrolls = db.query(Payroll).filter(
        func.date(Payroll.created_at) >= start_date,
        func.date(Payroll.created_at) <= end_date
    ).all()
    total_payroll = sum(p.net_salary for p in payrolls)

    # Calculate P&L
    gross_profit = total_revenue - cogs
    total_expenses = total_payroll  # Can add more expense categories later
    net_profit = gross_profit - total_expenses
    gross_margin = round(gross_profit / total_revenue * 100, 1) if total_revenue > 0 else 0
    net_margin = round(net_profit / total_revenue * 100, 1) if total_revenue > 0 else 0

    return {
        "period": {"start": str(start_date), "end": str(end_date)},
        "revenue": {
            "total_sales": round(total_revenue, 2),
            "gst_collected": round(total_sales_gst, 2),
            "discount_given": round(total_discount, 2)
        },
        "costs": {
            "cogs": round(cogs, 2),
            "purchases": round(total_purchases, 2),
            "payroll": round(total_payroll, 2),
            "total_expenses": round(cogs + total_expenses, 2)
        },
        "profit": {
            "gross_profit": round(gross_profit, 2),
            "gross_margin_percent": gross_margin,
            "net_profit": round(net_profit, 2),
            "net_margin_percent": net_margin
        }
    }


# ──────────────────────────────────────
# 4. Tax Report (GST summary)
# ──────────────────────────────────────
@router.get("/tax-report")
def tax_report(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """GST tax report — output tax (sales) vs input tax (purchases)"""

    # Output tax (sales)
    sales = db.query(Order).filter(
        Order.order_type == "sale",
        func.date(Order.created_at) >= start_date,
        func.date(Order.created_at) <= end_date
    ).all()

    output_gst = sum(o.gst_amount for o in sales)
    sales_subtotal = sum(o.subtotal for o in sales)

    # GST rate wise breakup (from order items)
    sale_order_ids = [o.id for o in sales]
    gst_breakup = defaultdict(lambda: {"taxable": 0, "gst": 0})
    if sale_order_ids:
        items = db.query(OrderItem).filter(OrderItem.order_id.in_(sale_order_ids)).all()
        for item in items:
            rate_key = f"{item.gst_rate}%"
            gst_breakup[rate_key]["taxable"] += item.unit_price * item.qty
            gst_breakup[rate_key]["gst"] += item.gst_amount

    # Input tax (purchases)
    purchases = db.query(PurchaseOrder).filter(
        PurchaseOrder.status.in_(["approved", "received"]),
        func.date(PurchaseOrder.created_at) >= start_date,
        func.date(PurchaseOrder.created_at) <= end_date
    ).all()

    input_gst = sum(po.gst_amount for po in purchases)
    purchase_subtotal = sum(po.subtotal for po in purchases)

    # Net GST payable
    net_gst = output_gst - input_gst

    gst_details = [
        {"rate": rate, "taxable_value": round(data["taxable"], 2), "gst_amount": round(data["gst"], 2)}
        for rate, data in sorted(gst_breakup.items())
    ]

    return {
        "period": {"start": str(start_date), "end": str(end_date)},
        "output_tax": {
            "sales_subtotal": round(sales_subtotal, 2),
            "total_output_gst": round(output_gst, 2),
            "total_bills": len(sales)
        },
        "input_tax": {
            "purchase_subtotal": round(purchase_subtotal, 2),
            "total_input_gst": round(input_gst, 2),
            "total_pos": len(purchases)
        },
        "net_gst_payable": round(net_gst, 2),
        "gst_rate_breakup": gst_details
    }


# ──────────────────────────────────────
# 5. Category-wise Sales Analysis
# ──────────────────────────────────────
@router.get("/category-analysis")
def category_analysis(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Category wise sales — kaunsi category sabse zyada bik rahi hai"""

    start_date = datetime.now() - timedelta(days=days)

    items = db.query(OrderItem).join(
        Order, Order.id == OrderItem.order_id
    ).filter(
        Order.order_type == "sale",
        Order.created_at >= start_date
    ).all()

    cat_data = defaultdict(lambda: {"qty": 0, "revenue": 0, "items_count": 0})

    for item in items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        category = product.category if product and product.category else "Uncategorized"
        cat_data[category]["qty"] += item.qty
        cat_data[category]["revenue"] += item.total
        cat_data[category]["items_count"] += 1

    total_revenue = sum(d["revenue"] for d in cat_data.values())

    categories = []
    for cat, data in sorted(cat_data.items(), key=lambda x: x[1]["revenue"], reverse=True):
        pct = round(data["revenue"] / total_revenue * 100, 1) if total_revenue > 0 else 0
        categories.append({
            "category": cat,
            "qty_sold": data["qty"],
            "revenue": round(data["revenue"], 2),
            "share_percent": pct,
            "items_in_bills": data["items_count"]
        })

    return {
        "period_days": days,
        "total_revenue": round(total_revenue, 2),
        "categories": categories
    }


# ──────────────────────────────────────
# 6. Payment Mode Analysis
# ──────────────────────────────────────
@router.get("/payment-analysis")
def payment_analysis(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """Payment mode wise breakup — cash/upi/card/udhaar trends"""

    start_date = datetime.now() - timedelta(days=days)

    orders = db.query(Order).filter(
        Order.order_type == "sale",
        Order.created_at >= start_date
    ).all()

    mode_data = defaultdict(lambda: {"count": 0, "total": 0})
    for o in orders:
        mode_data[o.payment_mode]["count"] += 1
        mode_data[o.payment_mode]["total"] += o.grand_total

    total = sum(d["total"] for d in mode_data.values())

    modes = []
    for mode, data in sorted(mode_data.items(), key=lambda x: x[1]["total"], reverse=True):
        pct = round(data["total"] / total * 100, 1) if total > 0 else 0
        modes.append({
            "mode": mode,
            "bills": data["count"],
            "amount": round(data["total"], 2),
            "share_percent": pct
        })

    return {
        "period_days": days,
        "total_amount": round(total, 2),
        "total_bills": len(orders),
        "modes": modes
    }


# ──────────────────────────────────────
# 7. Business Dashboard (all-in-one)
# ──────────────────────────────────────
@router.get("/dashboard")
def business_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ek screen pe poora business — aaj, week, month summary"""

    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    def get_sales(start, end):
        orders = db.query(Order).filter(
            Order.order_type == "sale",
            func.date(Order.created_at) >= start,
            func.date(Order.created_at) <= end
        ).all()
        return {"bills": len(orders), "revenue": round(sum(o.grand_total for o in orders), 2)}

    # Product stats
    active_products = db.query(func.count(Product.id)).filter(Product.is_active == True).scalar()
    low_stock = db.query(func.count(Product.id)).filter(
        Product.is_active == True, Product.stock_qty <= Product.reorder_level
    ).scalar()

    # Udhaar
    total_udhaar = db.query(func.sum(Dealer.outstanding)).scalar() or 0

    # Inventory value
    products = db.query(Product).filter(Product.is_active == True).all()
    stock_value = sum(p.stock_qty * (p.purchase_price or p.selling_price) for p in products)

    return {
        "today": get_sales(today, today),
        "this_week": get_sales(week_start, today),
        "this_month": get_sales(month_start, today),
        "inventory": {
            "active_products": active_products,
            "low_stock_alerts": low_stock,
            "stock_value": round(stock_value, 2)
        },
        "udhaar_outstanding": round(float(total_udhaar), 2),
        "generated_at": str(datetime.now())
    }

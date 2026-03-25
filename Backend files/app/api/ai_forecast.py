# SmartStore ERP — AI Demand Forecast API (Phase 11)
# Past sales data se future demand predict karo
# Simple statistical methods: Moving Average, Growth Trend, Seasonality

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
from app.models.user import User

router = APIRouter(prefix="/ai/forecast", tags=["AI - Demand Forecast"])


def get_daily_sales(db: Session, product_id: int, days: int = 90) -> dict:
    """Product ki daily sales nikalo last X days ki"""
    start_date = datetime.now() - timedelta(days=days)

    results = db.query(
        func.date(Order.created_at).label("sale_date"),
        func.sum(OrderItem.qty).label("total_qty"),
        func.sum(OrderItem.total).label("total_amount")
    ).join(OrderItem, Order.id == OrderItem.order_id).filter(
        OrderItem.product_id == product_id,
        Order.order_type == "sale",
        Order.created_at >= start_date
    ).group_by(func.date(Order.created_at)).all()

    daily = {}
    for r in results:
        daily[str(r.sale_date)] = {"qty": int(r.total_qty), "amount": float(r.total_amount)}
    return daily


def moving_average(values: list, window: int = 7) -> float:
    """Simple moving average — last X values ka average"""
    if not values:
        return 0.0
    window_values = values[-window:]
    return round(sum(window_values) / len(window_values), 2)


# ──────────────────────────────────────
# 1. Product Demand Forecast
# ──────────────────────────────────────
@router.get("/product/{product_id}")
def forecast_product(
    product_id: int,
    forecast_days: int = Query(7, ge=1, le=90, description="Kitne din ki forecast chahiye"),
    history_days: int = Query(90, ge=7, le=365, description="Kitne din ka past data use karo"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ek product ki demand forecast — next X days mein kitna bikega"""

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product nahi mila")

    daily_sales = get_daily_sales(db, product_id, history_days)

    if not daily_sales:
        return {
            "product_id": product_id,
            "product_name": product.name,
            "message": "Past sales data nahi hai — forecast possible nahi",
            "forecast": []
        }

    # Daily qty list banao (0 for days with no sales)
    all_days = []
    for i in range(history_days, 0, -1):
        day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        qty = daily_sales.get(day, {}).get("qty", 0)
        all_days.append(qty)

    # Moving averages calculate karo
    avg_7 = moving_average(all_days, 7)
    avg_30 = moving_average(all_days, 30)
    avg_overall = moving_average(all_days, len(all_days))

    # Growth trend — last 30 days vs previous 30 days
    if len(all_days) >= 60:
        recent_30 = sum(all_days[-30:])
        previous_30 = sum(all_days[-60:-30])
        if previous_30 > 0:
            growth_rate = round((recent_30 - previous_30) / previous_30 * 100, 1)
        else:
            growth_rate = 0.0
    else:
        growth_rate = 0.0

    # Forecast next X days — weighted average with trend
    trend_factor = 1 + (growth_rate / 100) if growth_rate != 0 else 1
    forecast = []
    for i in range(1, forecast_days + 1):
        forecast_date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
        # Weighted: 50% recent 7-day avg + 30% 30-day avg + 20% overall avg
        predicted_qty = round((avg_7 * 0.5 + avg_30 * 0.3 + avg_overall * 0.2) * trend_factor)
        predicted_qty = max(0, predicted_qty)
        forecast.append({
            "date": forecast_date,
            "predicted_qty": predicted_qty,
            "predicted_revenue": round(predicted_qty * product.selling_price, 2)
        })

    total_forecast_qty = sum(f["predicted_qty"] for f in forecast)
    stock_sufficient = product.stock_qty >= total_forecast_qty
    reorder_needed = not stock_sufficient

    return {
        "product_id": product_id,
        "product_name": product.name,
        "current_stock": product.stock_qty,
        "analysis": {
            "avg_daily_7day": avg_7,
            "avg_daily_30day": avg_30,
            "avg_daily_overall": avg_overall,
            "growth_trend_percent": growth_rate,
            "history_days_used": len(all_days),
            "total_sold_in_period": sum(all_days)
        },
        "forecast": forecast,
        "summary": {
            "forecast_days": forecast_days,
            "total_predicted_qty": total_forecast_qty,
            "total_predicted_revenue": round(sum(f["predicted_revenue"] for f in forecast), 2),
            "stock_sufficient": stock_sufficient,
            "reorder_needed": reorder_needed,
            "reorder_qty": max(0, total_forecast_qty - product.stock_qty) if reorder_needed else 0
        }
    }


# ──────────────────────────────────────
# 2. Top Selling Products (trending)
# ──────────────────────────────────────
@router.get("/trending")
def trending_products(
    days: int = Query(30, ge=1, le=365, description="Last X days ka data"),
    top_n: int = Query(10, ge=1, le=50, description="Top kitne products"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Top selling products — last X days mein sabse zyada kya bika"""

    start_date = datetime.now() - timedelta(days=days)

    results = db.query(
        OrderItem.product_id,
        OrderItem.product_name,
        func.sum(OrderItem.qty).label("total_qty"),
        func.sum(OrderItem.total).label("total_revenue"),
        func.count(OrderItem.id).label("times_sold")
    ).join(Order, Order.id == OrderItem.order_id).filter(
        Order.order_type == "sale",
        Order.created_at >= start_date
    ).group_by(OrderItem.product_id, OrderItem.product_name
    ).order_by(func.sum(OrderItem.qty).desc()
    ).limit(top_n).all()

    trending = []
    for r in results:
        product = db.query(Product).filter(Product.id == r.product_id).first()
        trending.append({
            "rank": len(trending) + 1,
            "product_id": r.product_id,
            "product_name": r.product_name,
            "total_qty_sold": int(r.total_qty),
            "total_revenue": round(float(r.total_revenue), 2),
            "times_in_bills": int(r.times_sold),
            "current_stock": product.stock_qty if product else 0
        })

    return {
        "period_days": days,
        "top_n": top_n,
        "trending_products": trending
    }


# ──────────────────────────────────────
# 3. Slow Moving Products (dead stock)
# ──────────────────────────────────────
@router.get("/slow-moving")
def slow_moving_products(
    days: int = Query(30, ge=1, le=365, description="Last X days mein check karo"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Wo products jo last X days mein bahut kam ya bilkul nahi bike"""

    start_date = datetime.now() - timedelta(days=days)

    # Products jinki sale hui
    sold_product_ids = db.query(OrderItem.product_id).join(
        Order, Order.id == OrderItem.order_id
    ).filter(
        Order.order_type == "sale",
        Order.created_at >= start_date
    ).distinct().all()
    sold_ids = {r[0] for r in sold_product_ids}

    # Active products jo nahi bike
    active_products = db.query(Product).filter(
        Product.is_active == True,
        Product.stock_qty > 0
    ).all()

    slow = []
    for p in active_products:
        if p.id not in sold_ids:
            stock_value = round(p.stock_qty * (p.purchase_price or p.selling_price), 2)
            slow.append({
                "product_id": p.id,
                "product_name": p.name,
                "category": p.category,
                "stock_qty": p.stock_qty,
                "stock_value": stock_value,
                "days_unsold": days
            })

    # Sort by stock value descending (highest value dead stock first)
    slow.sort(key=lambda x: x["stock_value"], reverse=True)

    total_dead_value = sum(s["stock_value"] for s in slow)

    return {
        "period_days": days,
        "total_slow_products": len(slow),
        "total_dead_stock_value": round(total_dead_value, 2),
        "slow_moving_products": slow
    }


# ──────────────────────────────────────
# 4. Reorder Suggestions (AI auto-suggest)
# ──────────────────────────────────────
@router.get("/reorder-suggestions")
def reorder_suggestions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner", "staff"]))
):
    """AI based reorder suggestions — kaunse products kab aur kitne mangwao"""

    # Last 30 days ki sales se average daily demand nikalo
    start_date = datetime.now() - timedelta(days=30)

    sales_data = db.query(
        OrderItem.product_id,
        func.sum(OrderItem.qty).label("total_qty")
    ).join(Order, Order.id == OrderItem.order_id).filter(
        Order.order_type == "sale",
        Order.created_at >= start_date
    ).group_by(OrderItem.product_id).all()

    sales_map = {r.product_id: int(r.total_qty) for r in sales_data}

    suggestions = []
    products = db.query(Product).filter(Product.is_active == True).all()

    for p in products:
        sold_30 = sales_map.get(p.id, 0)
        avg_daily = round(sold_30 / 30, 2)

        if avg_daily == 0:
            continue

        # Days of stock left
        days_left = round(p.stock_qty / avg_daily, 1) if avg_daily > 0 else 999

        # Reorder if less than 7 days stock
        if days_left <= 7:
            urgency = "URGENT" if days_left <= 3 else "SOON"
            # Suggest ordering 14 days worth of stock
            suggested_qty = max(1, round(avg_daily * 14) - p.stock_qty)

            suggestions.append({
                "product_id": p.id,
                "product_name": p.name,
                "current_stock": p.stock_qty,
                "avg_daily_sales": avg_daily,
                "days_of_stock_left": days_left,
                "urgency": urgency,
                "suggested_order_qty": suggested_qty,
                "estimated_cost": round(suggested_qty * (p.purchase_price or p.selling_price * 0.7), 2)
            })

    # Sort by urgency (least days first)
    suggestions.sort(key=lambda x: x["days_of_stock_left"])

    return {
        "total_suggestions": len(suggestions),
        "suggestions": suggestions
    }

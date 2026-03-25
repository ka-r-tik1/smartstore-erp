# SmartStore ERP — AI Fraud Detection API (Phase 11)
# Suspicious transactions detect karo — unusual amounts, patterns, anomalies
# Method: Z-Score anomaly detection (no ML library needed)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional
import math

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.order import Order, OrderItem
from app.models.payment import Payment
from app.models.product import Product
from app.models.user import User

router = APIRouter(prefix="/ai/fraud", tags=["AI - Fraud Detection"])


def calculate_z_score(value: float, mean: float, std_dev: float) -> float:
    """Z-Score = kitna door hai average se (standard deviations mein)"""
    if std_dev == 0:
        return 0.0
    return round((value - mean) / std_dev, 2)


def std_deviation(values: list) -> float:
    """Standard deviation calculate karo"""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return round(math.sqrt(variance), 2)


# ──────────────────────────────────────
# 1. Unusual Bill Amounts (Z-Score anomaly)
# ──────────────────────────────────────
@router.get("/unusual-bills")
def unusual_bills(
    days: int = Query(30, ge=1, le=365, description="Last X days check karo"),
    threshold: float = Query(2.0, ge=1.0, le=5.0, description="Z-Score threshold (2.0 = suspicious, 3.0 = highly suspicious)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """Bills jinki amount unusually high ya low hai — Z-Score se detect"""

    start_date = datetime.now() - timedelta(days=days)

    orders = db.query(Order).filter(
        Order.order_type == "sale",
        Order.created_at >= start_date
    ).all()

    if len(orders) < 5:
        return {"message": "Kam se kam 5 bills chahiye analysis ke liye", "suspicious_bills": []}

    amounts = [o.grand_total for o in orders]
    mean_amount = round(sum(amounts) / len(amounts), 2)
    std_dev = std_deviation(amounts)

    suspicious = []
    for o in orders:
        z = calculate_z_score(o.grand_total, mean_amount, std_dev)
        if abs(z) >= threshold:
            risk_level = "HIGH" if abs(z) >= 3.0 else "MEDIUM"
            suspicious.append({
                "order_id": o.id,
                "invoice_number": o.invoice_number,
                "amount": o.grand_total,
                "z_score": z,
                "risk_level": risk_level,
                "payment_mode": o.payment_mode,
                "date": str(o.created_at),
                "reason": "Amount bahut zyada hai" if z > 0 else "Amount bahut kam hai"
            })

    suspicious.sort(key=lambda x: abs(x["z_score"]), reverse=True)

    return {
        "period_days": days,
        "total_bills": len(orders),
        "average_bill": mean_amount,
        "std_deviation": std_dev,
        "threshold_used": threshold,
        "suspicious_count": len(suspicious),
        "suspicious_bills": suspicious
    }


# ──────────────────────────────────────
# 2. Unusual Discounts
# ──────────────────────────────────────
@router.get("/unusual-discounts")
def unusual_discounts(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """Bills jinme unusually high discount diya gaya — koi chori toh nahi?"""

    start_date = datetime.now() - timedelta(days=days)

    orders = db.query(Order).filter(
        Order.order_type == "sale",
        Order.discount > 0,
        Order.created_at >= start_date
    ).all()

    if not orders:
        return {"message": "Koi discount wali bill nahi mili", "suspicious_discounts": []}

    suspicious = []
    for o in orders:
        if o.subtotal > 0:
            discount_pct = round(o.discount / o.subtotal * 100, 1)
            # Flag if discount is more than 20% of subtotal
            if discount_pct > 20:
                risk_level = "HIGH" if discount_pct > 40 else "MEDIUM"
                suspicious.append({
                    "order_id": o.id,
                    "invoice_number": o.invoice_number,
                    "subtotal": o.subtotal,
                    "discount": o.discount,
                    "discount_percent": discount_pct,
                    "grand_total": o.grand_total,
                    "risk_level": risk_level,
                    "date": str(o.created_at),
                    "reason": f"Discount {discount_pct}% hai — zyada lag raha hai"
                })

    suspicious.sort(key=lambda x: x["discount_percent"], reverse=True)

    total_discount = sum(o.discount for o in orders)

    return {
        "period_days": days,
        "total_discount_bills": len(orders),
        "total_discount_given": round(total_discount, 2),
        "suspicious_count": len(suspicious),
        "suspicious_discounts": suspicious
    }


# ──────────────────────────────────────
# 3. Void/Cancel Pattern Detection
# ──────────────────────────────────────
@router.get("/void-patterns")
def void_patterns(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """Zyada returns/voids detect karo — possible employee fraud"""

    start_date = datetime.now() - timedelta(days=days)

    total_sales = db.query(func.count(Order.id)).filter(
        Order.order_type == "sale",
        Order.created_at >= start_date
    ).scalar() or 0

    total_returns = db.query(func.count(Order.id)).filter(
        Order.order_type == "return",
        Order.created_at >= start_date
    ).scalar() or 0

    return_rate = round(total_returns / total_sales * 100, 1) if total_sales > 0 else 0

    risk_level = "OK"
    if return_rate > 10:
        risk_level = "HIGH"
    elif return_rate > 5:
        risk_level = "MEDIUM"

    return {
        "period_days": days,
        "total_sales": total_sales,
        "total_returns": total_returns,
        "return_rate_percent": return_rate,
        "risk_level": risk_level,
        "message": "Return rate normal hai" if risk_level == "OK" else f"Return rate {return_rate}% — investigate karo!"
    }


# ──────────────────────────────────────
# 4. Cash vs Digital Mismatch
# ──────────────────────────────────────
@router.get("/payment-anomaly")
def payment_anomaly(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """Cash heavy bills detect karo — digital payment avoid ho rahi hai kya?"""

    start_date = datetime.now() - timedelta(days=days)

    orders = db.query(Order).filter(
        Order.order_type == "sale",
        Order.created_at >= start_date
    ).all()

    if not orders:
        return {"message": "Koi bill nahi mili is period mein"}

    mode_stats = {}
    for o in orders:
        mode = o.payment_mode or "unknown"
        if mode not in mode_stats:
            mode_stats[mode] = {"count": 0, "total": 0.0}
        mode_stats[mode]["count"] += 1
        mode_stats[mode]["total"] += o.grand_total

    total_amount = sum(s["total"] for s in mode_stats.values())
    total_bills = len(orders)

    breakdown = []
    for mode, stats in mode_stats.items():
        pct = round(stats["total"] / total_amount * 100, 1) if total_amount > 0 else 0
        breakdown.append({
            "payment_mode": mode,
            "bills": stats["count"],
            "amount": round(stats["total"], 2),
            "percentage": pct
        })

    breakdown.sort(key=lambda x: x["amount"], reverse=True)

    # Flag if cash > 70%
    cash_pct = next((b["percentage"] for b in breakdown if b["payment_mode"] == "cash"), 0)
    alert = ""
    if cash_pct > 70:
        alert = f"Cash transactions {cash_pct}% hain — digital payment push karo, fraud risk zyada"

    return {
        "period_days": days,
        "total_bills": total_bills,
        "total_amount": round(total_amount, 2),
        "payment_breakdown": breakdown,
        "alert": alert
    }


# ──────────────────────────────────────
# 5. Full Fraud Dashboard
# ──────────────────────────────────────
@router.get("/dashboard")
def fraud_dashboard(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """Ek jagah pe saare fraud indicators dekho"""

    start_date = datetime.now() - timedelta(days=days)

    # Bills
    orders = db.query(Order).filter(
        Order.order_type == "sale",
        Order.created_at >= start_date
    ).all()

    total_bills = len(orders)
    if total_bills == 0:
        return {"message": "Koi data nahi hai is period mein", "risk_score": 0}

    amounts = [o.grand_total for o in orders]
    mean_amount = sum(amounts) / len(amounts)
    std_dev = std_deviation(amounts)

    # Risk indicators
    unusual_amount_count = sum(1 for o in orders if abs(calculate_z_score(o.grand_total, mean_amount, std_dev)) >= 2.0)
    high_discount_count = sum(1 for o in orders if o.subtotal > 0 and o.discount / o.subtotal > 0.2)
    cash_orders = sum(1 for o in orders if o.payment_mode == "cash")
    cash_pct = round(cash_orders / total_bills * 100, 1)

    # Overall risk score (0-100)
    risk_score = 0
    risk_score += min(30, unusual_amount_count * 5)  # Unusual amounts
    risk_score += min(30, high_discount_count * 10)  # High discounts
    risk_score += min(20, max(0, cash_pct - 50))     # Cash heavy
    risk_score += min(20, 0)                          # Returns (future)

    risk_level = "LOW"
    if risk_score >= 60:
        risk_level = "HIGH"
    elif risk_score >= 30:
        risk_level = "MEDIUM"

    return {
        "period_days": days,
        "total_bills": total_bills,
        "risk_score": min(100, risk_score),
        "risk_level": risk_level,
        "indicators": {
            "unusual_bill_amounts": unusual_amount_count,
            "high_discount_bills": high_discount_count,
            "cash_percentage": cash_pct,
            "average_bill": round(mean_amount, 2)
        },
        "recommendations": [
            "Unusual amount bills manually check karo" if unusual_amount_count > 0 else None,
            "High discount bills ki approval process lagao" if high_discount_count > 0 else None,
            "Digital payments push karo" if cash_pct > 60 else None,
        ]
    }

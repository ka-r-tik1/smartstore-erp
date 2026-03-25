# SmartStore ERP — AI Chatbot API (Phase 11)
# Natural language mein data poocho — "aaj kitni sale hui?", "sabse zyada kya bika?"
# Simple keyword matching based NLP (no external library needed)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.dealer import Dealer
from app.models.inventory import StockBatch
from app.models.user import User

router = APIRouter(prefix="/ai/chatbot", tags=["AI - Chatbot"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500, description="Apna sawaal poocho")


class ChatResponse(BaseModel):
    question: str
    answer: str
    data: dict = {}


def parse_intent(message: str) -> tuple:
    """Message se intent aur entities nikalo — simple keyword matching"""
    msg = message.lower().strip()

    # Sale related
    if any(w in msg for w in ["sale", "sell", "biki", "bikri", "revenue", "kamai", "kamaayi"]):
        if any(w in msg for w in ["aaj", "today", "abhi"]):
            return ("sale_today", {})
        if any(w in msg for w in ["week", "hafta", "hafte"]):
            return ("sale_period", {"days": 7})
        if any(w in msg for w in ["month", "mahina", "mahine"]):
            return ("sale_period", {"days": 30})
        return ("sale_today", {})

    # Top/best selling
    if any(w in msg for w in ["top", "best", "sabse zyada", "popular", "trending", "hit"]):
        return ("top_products", {})

    # Stock related
    if any(w in msg for w in ["stock", "maal", "inventory", "godown"]):
        if any(w in msg for w in ["low", "kam", "khatam", "alert", "shortage"]):
            return ("low_stock", {})
        if any(w in msg for w in ["value", "total", "kitna", "worth"]):
            return ("stock_value", {})
        return ("stock_summary", {})

    # Expiry related
    if any(w in msg for w in ["expiry", "expire", "kharab", "date"]):
        return ("expiry_alert", {})

    # Dealer/Udhaar related
    if any(w in msg for w in ["udhaar", "credit", "outstanding", "baaki", "dealer"]):
        return ("udhaar_summary", {})

    # Product count
    if any(w in msg for w in ["kitne product", "total product", "product count", "products hain"]):
        return ("product_count", {})

    # Profit
    if any(w in msg for w in ["profit", "margin", "munafa", "fayda"]):
        return ("profit_estimate", {})

    # Help
    if any(w in msg for w in ["help", "madad", "kya pooch sakta", "kya puch", "commands"]):
        return ("help", {})

    return ("unknown", {})


# ──────────────────────────────────────
# Chat Endpoint
# ──────────────────────────────────────
@router.post("/ask", response_model=ChatResponse)
def ask_chatbot(
    chat: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Chatbot se sawaal poocho — Hinglish mein bhi chal jayega!"""

    intent, params = parse_intent(chat.message)

    # ── Sale Today ──
    if intent == "sale_today":
        today = datetime.now().date()
        orders = db.query(Order).filter(
            func.date(Order.created_at) == today,
            Order.order_type == "sale"
        ).all()

        total = sum(o.grand_total for o in orders)
        count = len(orders)

        return ChatResponse(
            question=chat.message,
            answer=f"Aaj ki sale: Rs {total:.2f} ({count} bills)",
            data={"total_sale": round(total, 2), "total_bills": count, "date": str(today)}
        )

    # ── Sale Period ──
    if intent == "sale_period":
        days = params.get("days", 7)
        start = datetime.now() - timedelta(days=days)
        orders = db.query(Order).filter(
            Order.created_at >= start,
            Order.order_type == "sale"
        ).all()

        total = sum(o.grand_total for o in orders)
        count = len(orders)
        label = "hafte" if days == 7 else "mahine"

        return ChatResponse(
            question=chat.message,
            answer=f"Last {days} din ({label}) ki sale: Rs {total:.2f} ({count} bills)",
            data={"total_sale": round(total, 2), "total_bills": count, "days": days}
        )

    # ── Top Products ──
    if intent == "top_products":
        start = datetime.now() - timedelta(days=30)
        results = db.query(
            OrderItem.product_name,
            func.sum(OrderItem.qty).label("total_qty")
        ).join(Order, Order.id == OrderItem.order_id).filter(
            Order.order_type == "sale",
            Order.created_at >= start
        ).group_by(OrderItem.product_name
        ).order_by(func.sum(OrderItem.qty).desc()
        ).limit(5).all()

        if not results:
            return ChatResponse(question=chat.message, answer="Abhi tak koi sale nahi hui", data={})

        top_list = [{"name": r.product_name, "qty": int(r.total_qty)} for r in results]
        top_names = ", ".join(f"{r.product_name} ({int(r.total_qty)} pcs)" for r in results)

        return ChatResponse(
            question=chat.message,
            answer=f"Top 5 products (last 30 days): {top_names}",
            data={"top_products": top_list}
        )

    # ── Low Stock ──
    if intent == "low_stock":
        products = db.query(Product).filter(
            Product.is_active == True,
            Product.stock_qty <= Product.reorder_level
        ).order_by(Product.stock_qty).limit(10).all()

        if not products:
            return ChatResponse(question=chat.message, answer="Abhi koi low stock nahi hai — sab theek hai!", data={})

        items = [{"name": p.name, "stock": p.stock_qty, "reorder": p.reorder_level} for p in products]
        names = ", ".join(f"{p.name} ({p.stock_qty})" for p in products[:5])

        return ChatResponse(
            question=chat.message,
            answer=f"Low stock alerts: {names}",
            data={"low_stock_products": items, "total_low": len(products)}
        )

    # ── Stock Summary ──
    if intent == "stock_summary" or intent == "stock_value":
        products = db.query(Product).filter(Product.is_active == True).all()
        total_qty = sum(p.stock_qty for p in products)
        total_value = sum(p.stock_qty * (p.purchase_price or p.selling_price) for p in products)

        return ChatResponse(
            question=chat.message,
            answer=f"Total stock: {total_qty} items, worth Rs {total_value:.2f} ({len(products)} products)",
            data={"total_products": len(products), "total_qty": total_qty, "total_value": round(total_value, 2)}
        )

    # ── Expiry Alert ──
    if intent == "expiry_alert":
        from datetime import date
        cutoff = date.today() + timedelta(days=30)
        batches = db.query(StockBatch).filter(
            StockBatch.expiry_date != None,
            StockBatch.expiry_date <= cutoff,
            StockBatch.qty > 0
        ).all()

        if not batches:
            return ChatResponse(question=chat.message, answer="Next 30 din mein koi product expire nahi ho raha", data={})

        items = []
        for b in batches:
            product = db.query(Product).filter(Product.id == b.product_id).first()
            items.append({
                "product": product.name if product else "Unknown",
                "batch": b.batch_number,
                "qty": b.qty,
                "expiry": str(b.expiry_date)
            })

        return ChatResponse(
            question=chat.message,
            answer=f"{len(batches)} batches next 30 din mein expire hongi",
            data={"expiring_batches": items}
        )

    # ── Udhaar Summary ──
    if intent == "udhaar_summary":
        dealers = db.query(Dealer).filter(Dealer.outstanding > 0).all()
        total_udhaar = sum(d.outstanding for d in dealers)

        if not dealers:
            return ChatResponse(question=chat.message, answer="Kisi ka udhaar baaki nahi hai!", data={})

        top_debtors = sorted(dealers, key=lambda d: d.outstanding, reverse=True)[:5]
        names = ", ".join(f"{d.name} (Rs {d.outstanding:.0f})" for d in top_debtors)

        return ChatResponse(
            question=chat.message,
            answer=f"Total udhaar baaki: Rs {total_udhaar:.2f} ({len(dealers)} dealers). Top: {names}",
            data={"total_udhaar": round(total_udhaar, 2), "dealers_with_udhaar": len(dealers)}
        )

    # ── Product Count ──
    if intent == "product_count":
        active = db.query(func.count(Product.id)).filter(Product.is_active == True).scalar()
        total = db.query(func.count(Product.id)).scalar()

        return ChatResponse(
            question=chat.message,
            answer=f"Total products: {total} (Active: {active})",
            data={"total": total, "active": active}
        )

    # ── Profit Estimate ──
    if intent == "profit_estimate":
        start = datetime.now() - timedelta(days=30)
        orders = db.query(Order).filter(
            Order.order_type == "sale",
            Order.created_at >= start
        ).all()

        total_revenue = sum(o.grand_total for o in orders)
        # Rough estimate: 20-30% margin on FMCG
        est_profit = round(total_revenue * 0.25, 2)

        return ChatResponse(
            question=chat.message,
            answer=f"Last 30 din ki sale: Rs {total_revenue:.2f}. Estimated profit (~25%): Rs {est_profit:.2f}",
            data={"revenue_30d": round(total_revenue, 2), "estimated_profit": est_profit}
        )

    # ── Help ──
    if intent == "help":
        return ChatResponse(
            question=chat.message,
            answer="Ye pooch sakte ho: 'aaj kitni sale hui?', 'top products', 'low stock', 'expiry alert', 'udhaar kitna baaki', 'stock value', 'profit kitna', 'kitne products hain'",
            data={"supported_queries": [
                "aaj ki sale", "hafte ki sale", "mahine ki sale",
                "top products", "trending products",
                "low stock", "stock value",
                "expiry alert", "udhaar baaki",
                "kitne products", "profit"
            ]}
        )

    # ── Unknown ──
    return ChatResponse(
        question=chat.message,
        answer="Ye samajh nahi aaya. Try karo: 'aaj ki sale', 'top products', 'low stock', 'udhaar kitna'. Ya 'help' likho.",
        data={}
    )

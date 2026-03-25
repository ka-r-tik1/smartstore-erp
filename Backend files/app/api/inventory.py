# SmartStore ERP — Inventory API
# Stock In/Out with log, Low Stock Alerts, Expiry Tracking, Batch Management

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, timedelta

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.product import Product
from app.models.inventory import StockMovement, StockBatch
from app.models.user import User
from app.schemas.inventory import (
    StockInRequest, StockOutRequest,
    StockMovementResponse, StockBatchResponse,
    LowStockAlert, ExpiryAlert
)

router = APIRouter(prefix="/inventory", tags=["Inventory"])


# ──────────────────────────────────────
# 1. Stock In — Naya maal aaya (with batch + expiry)
# ──────────────────────────────────────
@router.post("/stock-in", response_model=StockMovementResponse, status_code=201)
def stock_in(
    data: StockInRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner", "staff"]))
):
    """Stock add karo — purchase/return/adjustment + optional batch with expiry"""

    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product nahi mila")

    stock_before = product.stock_qty

    # Product stock badhao
    product.stock_qty += data.qty

    # Stock movement log banao
    movement = StockMovement(
        product_id=data.product_id,
        movement_type=data.movement_type,
        qty=data.qty,
        stock_before=stock_before,
        stock_after=product.stock_qty,
        reference=data.reference,
        notes=data.notes,
        created_by=current_user.username
    )
    db.add(movement)

    # Batch banao — purchase_price ya expiry_date ya batch_number ho to
    if data.purchase_price or data.batch_number or data.expiry_date:
        batch = StockBatch(
            product_id=data.product_id,
            batch_number=data.batch_number,
            qty=data.qty,
            purchase_price=data.purchase_price,
            expiry_date=data.expiry_date,
            notes=data.notes
        )
        db.add(batch)

    # Product ka purchase_price update karo (latest price)
    if data.purchase_price:
        product.purchase_price = data.purchase_price

    db.commit()
    db.refresh(movement)
    return movement


# ──────────────────────────────────────
# 2. Stock Out — Maal gaya (damage/wastage/adjustment)
# ──────────────────────────────────────
@router.post("/stock-out", response_model=StockMovementResponse, status_code=201)
def stock_out(
    data: StockOutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner", "staff"]))
):
    """Stock minus karo — damage/wastage/adjustment"""

    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product nahi mila")

    if product.stock_qty < data.qty:
        raise HTTPException(
            status_code=400,
            detail=f"Stock sirf {product.stock_qty} hai, {data.qty} nahi nikal sakte"
        )

    stock_before = product.stock_qty
    product.stock_qty -= data.qty

    movement = StockMovement(
        product_id=data.product_id,
        movement_type=data.movement_type,
        qty=-data.qty,
        stock_before=stock_before,
        stock_after=product.stock_qty,
        reference=data.reference,
        notes=data.notes,
        created_by=current_user.username
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement


# ──────────────────────────────────────
# 3. Stock Movement History (kab kya hua)
# ──────────────────────────────────────
@router.get("/movements", response_model=list[StockMovementResponse])
def list_movements(
    product_id: Optional[int] = Query(None, description="Product ID se filter"),
    movement_type: Optional[str] = Query(None, description="purchase_in / sale_out / damage_out / etc."),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Stock movement history — kab, kitna, kyun stock change hua"""

    query = db.query(StockMovement)

    if product_id:
        query = query.filter(StockMovement.product_id == product_id)
    if movement_type:
        query = query.filter(StockMovement.movement_type == movement_type)

    movements = query.order_by(StockMovement.created_at.desc()).offset(skip).limit(limit).all()
    return movements


# ──────────────────────────────────────
# 4. Low Stock Alerts — Reorder level se neeche
# ──────────────────────────────────────
@router.get("/low-stock", response_model=list[LowStockAlert])
def low_stock_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Wo products jinki stock reorder level se neeche hai"""

    products = db.query(Product).filter(
        Product.is_active == True,
        Product.stock_qty <= Product.reorder_level
    ).order_by(Product.stock_qty).all()

    alerts = []
    for p in products:
        alerts.append(LowStockAlert(
            product_id=p.id,
            product_name=p.name,
            current_stock=p.stock_qty,
            reorder_level=p.reorder_level,
            shortage=p.reorder_level - p.stock_qty
        ))

    return alerts


# ──────────────────────────────────────
# 5. Expiry Alerts — Expiry date near items
# ──────────────────────────────────────
@router.get("/expiry-alerts", response_model=list[ExpiryAlert])
def expiry_alerts(
    days: int = Query(30, ge=1, le=365, description="Kitne din mein expire hone wale dikhao"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Wo batches jo next X din mein expire hone wali hain"""

    cutoff_date = date.today() + timedelta(days=days)

    batches = db.query(StockBatch).filter(
        StockBatch.expiry_date != None,
        StockBatch.expiry_date <= cutoff_date,
        StockBatch.qty > 0
    ).order_by(StockBatch.expiry_date).all()

    alerts = []
    for b in batches:
        product = db.query(Product).filter(Product.id == b.product_id).first()
        product_name = product.name if product else "Unknown"
        days_left = (b.expiry_date - date.today()).days

        alerts.append(ExpiryAlert(
            batch_id=b.id,
            product_id=b.product_id,
            product_name=product_name,
            batch_number=b.batch_number,
            qty=b.qty,
            expiry_date=b.expiry_date,
            days_left=days_left
        ))

    return alerts


# ──────────────────────────────────────
# 6a. Price History — Product ka purchase price history (dropdown ke liye)
# ──────────────────────────────────────
@router.get("/price-history/{product_id}")
def price_history(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Product ke last purchase prices — Stock In dropdown ke liye"""

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product nahi mila")

    batches = db.query(StockBatch).filter(
        StockBatch.product_id == product_id,
        StockBatch.purchase_price != None
    ).order_by(StockBatch.created_at.desc()).limit(20).all()

    seen = set()
    prices = []
    for b in batches:
        p = round(b.purchase_price, 2)
        if p not in seen:
            seen.add(p)
            prices.append({
                "price": p,
                "date": b.created_at.strftime("%d %b") if b.created_at else None
            })
        if len(prices) >= 5:
            break

    # Fallback: agar batch history nahi — purchase_price ya selling_price use karo
    if not prices:
        if product.purchase_price:
            prices.append({"price": round(product.purchase_price, 2)})
        if product.selling_price:
            prices.append({"price": round(product.selling_price, 2)})

    return {
        "product_id": product_id,
        "product_name": product.name,
        "current_purchase_price": product.purchase_price,
        "price_history": prices
    }


# ──────────────────────────────────────
# 6. Batches list (product ke saare batches)
# ──────────────────────────────────────
@router.get("/batches/{product_id}", response_model=list[StockBatchResponse])
def list_batches(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ek product ke saare batches — expiry date ke saath"""

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product nahi mila")

    batches = db.query(StockBatch).filter(
        StockBatch.product_id == product_id,
        StockBatch.qty > 0
    ).order_by(StockBatch.expiry_date).all()

    return batches


# ──────────────────────────────────────
# 7. Inventory Summary — Full stock overview
# ──────────────────────────────────────
@router.get("/summary")
def inventory_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Full inventory summary — total products, stock value, low stock count"""

    active_products = db.query(Product).filter(Product.is_active == True).all()

    total_products = len(active_products)
    total_stock_qty = sum(p.stock_qty for p in active_products)
    total_stock_value = sum(p.stock_qty * (p.purchase_price or p.selling_price) for p in active_products)
    total_retail_value = sum(p.stock_qty * p.selling_price for p in active_products)
    low_stock_count = sum(1 for p in active_products if p.stock_qty <= p.reorder_level)

    return {
        "total_products": total_products,
        "total_stock_qty": total_stock_qty,
        "total_stock_value": round(total_stock_value, 2),
        "total_retail_value": round(total_retail_value, 2),
        "potential_profit": round(total_retail_value - total_stock_value, 2),
        "low_stock_count": low_stock_count
    }

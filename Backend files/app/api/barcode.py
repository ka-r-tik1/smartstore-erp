# SmartStore ERP — Barcode API (Phase 10)
# Barcode generate karo, scan se product dhundho, bulk barcode generate

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import hashlib
import time

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.product import Product
from app.models.user import User

router = APIRouter(prefix="/barcode", tags=["Barcode"])


def generate_ean13(product_id: int) -> str:
    """EAN-13 format barcode generate karo — 13 digit unique number"""
    # SmartStore prefix (890 = India country code) + product based digits
    base = f"890{product_id:09d}"  # 12 digits

    # EAN-13 check digit calculate karo
    total = 0
    for i, digit in enumerate(base):
        if i % 2 == 0:
            total += int(digit)
        else:
            total += int(digit) * 3
    check_digit = (10 - (total % 10)) % 10

    return base + str(check_digit)


# ──────────────────────────────────────
# 1. Barcode Generate karo (for a product)
# ──────────────────────────────────────
@router.post("/generate/{product_id}")
def generate_barcode(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner", "staff"]))
):
    """Product ke liye EAN-13 barcode generate karo aur save karo"""

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product nahi mila")

    if product.barcode:
        return {
            "message": "Product pe barcode pehle se hai",
            "product_id": product_id,
            "product_name": product.name,
            "barcode": product.barcode,
            "already_exists": True
        }

    # EAN-13 barcode generate karo
    barcode = generate_ean13(product_id)

    # Duplicate check (rare but safe)
    existing = db.query(Product).filter(Product.barcode == barcode).first()
    if existing:
        # Timestamp add karke unique banao
        barcode = generate_ean13(product_id + int(time.time()) % 10000)

    product.barcode = barcode
    db.commit()

    return {
        "message": "Barcode generated!",
        "product_id": product_id,
        "product_name": product.name,
        "barcode": barcode,
        "already_exists": False
    }


# ──────────────────────────────────────
# 2. Barcode Scan — product dhundho
# ──────────────────────────────────────
@router.get("/scan/{barcode}")
def scan_barcode(
    barcode: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Barcode scan karo — product ki detail mil jayegi (POS billing ke liye)"""

    product = db.query(Product).filter(Product.barcode == barcode).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Barcode '{barcode}' se koi product nahi mila")

    if not product.is_active:
        raise HTTPException(status_code=400, detail=f"Product '{product.name}' discontinued hai")

    stock_alert = ""
    if product.stock_qty <= 0:
        stock_alert = "OUT OF STOCK!"
    elif product.stock_qty <= product.reorder_level:
        stock_alert = f"LOW STOCK! Sirf {product.stock_qty} bacha hai"

    return {
        "product_id": product.id,
        "name": product.name,
        "name_mr": product.name_mr,
        "barcode": product.barcode,
        "category": product.category,
        "brand": product.brand,
        "mrp": product.mrp,
        "selling_price": product.selling_price,
        "gst_rate": product.gst_rate,
        "stock_qty": product.stock_qty,
        "unit": product.unit,
        "stock_alert": stock_alert
    }


# ──────────────────────────────────────
# 3. Bulk Barcode Generate — sabhi products ke liye
# ──────────────────────────────────────
@router.post("/generate-bulk")
def generate_bulk_barcodes(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """Sabhi bina-barcode products ke liye ek saath barcode generate karo"""

    products = db.query(Product).filter(
        Product.is_active == True,
        (Product.barcode == None) | (Product.barcode == "")
    ).all()

    if not products:
        return {"message": "Sabhi products pe barcode already hai!", "generated": 0}

    results = []
    for product in products:
        barcode = generate_ean13(product.id)

        # Duplicate check
        existing = db.query(Product).filter(Product.barcode == barcode).first()
        if existing:
            barcode = generate_ean13(product.id + int(time.time()) % 10000)

        product.barcode = barcode
        results.append({
            "product_id": product.id,
            "product_name": product.name,
            "barcode": barcode
        })

    db.commit()

    return {
        "message": f"{len(results)} products ko barcode diya!",
        "generated": len(results),
        "products": results
    }


# ──────────────────────────────────────
# 4. Products without barcode — list
# ──────────────────────────────────────
@router.get("/missing")
def products_without_barcode(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Wo products jinpe barcode nahi hai"""

    products = db.query(Product).filter(
        Product.is_active == True,
        (Product.barcode == None) | (Product.barcode == "")
    ).all()

    return {
        "total_without_barcode": len(products),
        "products": [
            {"id": p.id, "name": p.name, "category": p.category, "brand": p.brand}
            for p in products
        ]
    }

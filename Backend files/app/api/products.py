# SmartStore ERP — Products API
# Product add karo, list karo, search karo, update karo, delete karo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse

router = APIRouter(prefix="/products", tags=["Products"])


# ──────────────────────────────────────
# 1. Product Add karo (Owner/Staff only)
# ──────────────────────────────────────
@router.post("/", response_model=ProductResponse, status_code=201)
def add_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner", "staff"]))
):
    """Naya product add karo — Owner ya Staff hi kar sakta hai"""

    # Barcode duplicate check
    if product.barcode:
        existing = db.query(Product).filter(Product.barcode == product.barcode).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Barcode '{product.barcode}' already exists")

    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


# ──────────────────────────────────────
# 2. Saare Products list karo (with search + filter)
# ──────────────────────────────────────
@router.get("/", response_model=list[ProductResponse])
def list_products(
    search: Optional[str] = Query(None, description="Name ya barcode se search karo"),
    category: Optional[str] = Query(None, description="Category se filter karo"),
    brand: Optional[str] = Query(None, description="Brand se filter karo"),
    active_only: bool = Query(True, description="Sirf active products dikhao"),
    skip: int = Query(0, ge=0, description="Kitne skip karo (pagination)"),
    limit: int = Query(50, ge=1, le=200, description="Kitne dikhao (max 200)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Products ki list — search, filter, pagination sab supported"""

    query = db.query(Product)

    # Active filter
    if active_only:
        query = query.filter(Product.is_active == True)

    # Search — name ya barcode mein match karo
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Product.name.ilike(search_term)) |
            (Product.barcode.ilike(search_term)) |
            (Product.name_mr.ilike(search_term))
        )

    # Category filter
    if category:
        query = query.filter(Product.category.ilike(f"%{category}%"))

    # Brand filter
    if brand:
        query = query.filter(Product.brand.ilike(f"%{brand}%"))

    # Pagination + return
    products = query.order_by(Product.name).offset(skip).limit(limit).all()
    return products


# ──────────────────────────────────────
# 3. Ek Product ki detail (by ID)
# ──────────────────────────────────────
@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Product ki full detail by ID"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product nahi mila")
    return product


# ──────────────────────────────────────
# 4. Product Update karo (Owner/Staff only)
# ──────────────────────────────────────
@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner", "staff"]))
):
    """Product update karo — sirf jo fields bhejo wo update hongi"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product nahi mila")

    # Barcode duplicate check (agar change ho raha hai)
    update_data = product_update.model_dump(exclude_unset=True)
    if "barcode" in update_data and update_data["barcode"]:
        existing = db.query(Product).filter(
            Product.barcode == update_data["barcode"],
            Product.id != product_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Barcode '{update_data['barcode']}' already exists")

    # Update fields
    for key, value in update_data.items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return product


# ──────────────────────────────────────
# 5. Product Delete karo (Soft delete — Owner only)
# ──────────────────────────────────────
@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """Product soft delete — is_active = False kar do. Sirf Owner kar sakta hai"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product nahi mila")

    product.is_active = False
    db.commit()
    return {"message": f"Product '{product.name}' deactivated", "id": product_id}


# ──────────────────────────────────────
# 6. Stock Update karo (quick stock adjustment)
# ──────────────────────────────────────
@router.patch("/{product_id}/stock")
def update_stock(
    product_id: int,
    qty: int = Query(..., description="+ mein add, - mein minus karo"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner", "staff"]))
):
    """Quick stock update — +10 ya -5 bhejo"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product nahi mila")

    new_stock = product.stock_qty + qty
    if new_stock < 0:
        raise HTTPException(status_code=400, detail=f"Stock negative nahi ho sakta. Current: {product.stock_qty}")

    product.stock_qty = new_stock
    db.commit()

    alert = ""
    if new_stock <= product.reorder_level:
        alert = f" ⚠️ LOW STOCK! Reorder level: {product.reorder_level}"

    return {
        "message": f"Stock updated: {product.name}",
        "old_stock": product.stock_qty - qty,
        "change": qty,
        "new_stock": new_stock,
        "alert": alert
    }

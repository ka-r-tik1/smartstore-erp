# SmartStore ERP — Invoice Auto Parser API (Phase 12)
# Purchase invoice upload karo (CSV/text), auto-parse karke PO + stock create karo
# Real OCR ke bina — CSV/structured text se data extract karo

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date
from typing import Optional
import csv
import io

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.product import Product
from app.models.dealer import Dealer
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.inventory import StockMovement, StockBatch
from app.models.order import Order, OrderItem
from app.models.user import User

router = APIRouter(prefix="/invoice-auto", tags=["Invoice Auto Parser"])


def generate_po_number(db: Session) -> str:
    """PO number generate — PO-2026-XXXX format"""
    year = datetime.now().year
    prefix = f"PO-{year}-"
    last_po = db.query(PurchaseOrder).filter(
        PurchaseOrder.po_number.like(f"{prefix}%")
    ).order_by(PurchaseOrder.id.desc()).first()

    if last_po:
        last_num = int(last_po.po_number.split("-")[-1])
        new_num = last_num + 1
    else:
        new_num = 1
    return f"{prefix}{new_num:04d}"


# ──────────────────────────────────────
# 1. Upload Purchase Invoice CSV — auto PO + stock
# ──────────────────────────────────────
@router.post("/upload-csv")
async def upload_invoice_csv(
    supplier_id: int = Query(..., description="Supplier ka ID"),
    auto_stock: bool = Query(True, description="Stock auto-update karo?"),
    file: UploadFile = File(..., description="CSV file — columns: product_name/barcode, qty, unit_price, batch_number(optional), expiry_date(optional)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner", "staff"]))
):
    """CSV file upload karo — auto purchase order ban jayega, stock bhi update hoga"""

    # Supplier check
    supplier = db.query(Dealer).filter(Dealer.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier nahi mila")

    # File type check
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Sirf CSV file upload karo")

    # CSV read karo
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))

    po_number = generate_po_number(db)
    po_items = []
    errors = []
    subtotal = 0.0
    total_gst = 0.0
    row_num = 0

    for row in reader:
        row_num += 1

        # Product dhundho — barcode ya name se
        product = None
        product_ref = row.get("barcode", "").strip() or row.get("product_name", "").strip() or row.get("name", "").strip()

        if not product_ref:
            errors.append(f"Row {row_num}: product_name ya barcode missing")
            continue

        # Barcode se dhundho
        if row.get("barcode", "").strip():
            product = db.query(Product).filter(Product.barcode == row["barcode"].strip()).first()

        # Name se dhundho
        if not product:
            product = db.query(Product).filter(
                Product.name.ilike(f"%{product_ref}%")
            ).first()

        if not product:
            errors.append(f"Row {row_num}: Product '{product_ref}' nahi mila database mein")
            continue

        # Qty parse karo
        try:
            qty = int(row.get("qty", "0").strip())
            if qty <= 0:
                errors.append(f"Row {row_num}: qty 0 ya negative hai")
                continue
        except ValueError:
            errors.append(f"Row {row_num}: qty '{row.get('qty', '')}' valid number nahi hai")
            continue

        # Unit price parse karo
        try:
            unit_price = float(row.get("unit_price", "0").strip())
            if unit_price <= 0:
                errors.append(f"Row {row_num}: unit_price 0 ya negative hai")
                continue
        except ValueError:
            errors.append(f"Row {row_num}: unit_price '{row.get('unit_price', '')}' valid nahi hai")
            continue

        # Batch & Expiry (optional)
        batch_number = row.get("batch_number", "").strip() or None
        expiry_str = row.get("expiry_date", "").strip()
        expiry_date = None
        if expiry_str:
            for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"]:
                try:
                    expiry_date = datetime.strptime(expiry_str, fmt).date()
                    break
                except ValueError:
                    continue

        # Calculate amounts
        item_subtotal = unit_price * qty
        item_gst = round(item_subtotal * product.gst_rate / 100, 2)
        item_total = round(item_subtotal + item_gst, 2)

        po_items.append({
            "product": product,
            "qty": qty,
            "unit_price": unit_price,
            "gst_rate": product.gst_rate,
            "gst_amount": item_gst,
            "total": item_total,
            "batch_number": batch_number,
            "expiry_date": expiry_date
        })

        subtotal += item_subtotal
        total_gst += item_gst

    if not po_items:
        return {
            "message": "Koi valid item nahi mila CSV mein",
            "errors": errors,
            "created": False
        }

    # PO create karo
    po = PurchaseOrder(
        po_number=po_number,
        supplier_id=supplier_id,
        status="received" if auto_stock else "draft",
        subtotal=round(subtotal, 2),
        gst_amount=round(total_gst, 2),
        grand_total=round(subtotal + total_gst, 2),
        received_date=date.today() if auto_stock else None,
        notes=f"Auto-imported from CSV: {file.filename}",
        created_by=current_user.username
    )
    db.add(po)
    db.flush()

    created_items = []
    for item_data in po_items:
        product = item_data["product"]

        po_item = PurchaseOrderItem(
            po_id=po.id,
            product_id=product.id,
            product_name=product.name,
            qty_ordered=item_data["qty"],
            qty_received=item_data["qty"] if auto_stock else 0,
            unit_price=item_data["unit_price"],
            gst_rate=item_data["gst_rate"],
            gst_amount=item_data["gst_amount"],
            total=item_data["total"]
        )
        db.add(po_item)

        # Auto stock update
        if auto_stock:
            stock_before = product.stock_qty
            product.stock_qty += item_data["qty"]

            # Stock movement log
            movement = StockMovement(
                product_id=product.id,
                movement_type="purchase_in",
                qty=item_data["qty"],
                stock_before=stock_before,
                stock_after=product.stock_qty,
                reference=po_number,
                notes=f"CSV import: {file.filename}",
                created_by=current_user.username
            )
            db.add(movement)

            # Batch create (agar batch/expiry hai)
            if item_data["batch_number"] or item_data["expiry_date"]:
                batch = StockBatch(
                    product_id=product.id,
                    batch_number=item_data["batch_number"],
                    qty=item_data["qty"],
                    purchase_price=item_data["unit_price"],
                    expiry_date=item_data["expiry_date"]
                )
                db.add(batch)

        created_items.append({
            "product_name": product.name,
            "qty": item_data["qty"],
            "unit_price": item_data["unit_price"],
            "total": item_data["total"],
            "stock_updated": auto_stock
        })

    db.commit()

    return {
        "message": f"Invoice parsed! PO {po_number} created.",
        "created": True,
        "po_number": po_number,
        "po_id": po.id,
        "supplier": supplier.name,
        "total_items": len(created_items),
        "grand_total": round(subtotal + total_gst, 2),
        "stock_auto_updated": auto_stock,
        "items": created_items,
        "errors": errors if errors else None
    }


# ──────────────────────────────────────
# 2. Parse Invoice Text (manual paste)
# ──────────────────────────────────────
@router.post("/parse-text")
def parse_invoice_text(
    text: str = Query(..., description="Invoice text paste karo — format: product_name, qty, price (per line)"),
    supplier_id: int = Query(..., description="Supplier ka ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner", "staff"]))
):
    """Invoice text paste karo — har line mein: product_name, qty, unit_price"""

    supplier = db.query(Dealer).filter(Dealer.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier nahi mila")

    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    parsed_items = []
    errors = []

    for i, line in enumerate(lines, 1):
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 3:
            errors.append(f"Line {i}: kam se kam 3 values chahiye (name, qty, price). Got: '{line}'")
            continue

        product_name = parts[0]
        try:
            qty = int(parts[1])
            unit_price = float(parts[2])
        except ValueError:
            errors.append(f"Line {i}: qty ya price valid nahi — '{line}'")
            continue

        # Product match karo
        product = db.query(Product).filter(
            Product.name.ilike(f"%{product_name}%")
        ).first()

        if product:
            gst = round(unit_price * qty * product.gst_rate / 100, 2)
            parsed_items.append({
                "product_id": product.id,
                "product_name": product.name,
                "matched": True,
                "qty": qty,
                "unit_price": unit_price,
                "gst_rate": product.gst_rate,
                "gst_amount": gst,
                "total": round(unit_price * qty + gst, 2)
            })
        else:
            parsed_items.append({
                "product_id": None,
                "product_name": product_name,
                "matched": False,
                "qty": qty,
                "unit_price": unit_price,
                "gst_rate": 0,
                "gst_amount": 0,
                "total": round(unit_price * qty, 2)
            })

    matched = [i for i in parsed_items if i["matched"]]
    unmatched = [i for i in parsed_items if not i["matched"]]

    return {
        "total_lines": len(lines),
        "parsed_items": len(parsed_items),
        "matched": len(matched),
        "unmatched": len(unmatched),
        "items": parsed_items,
        "errors": errors if errors else None,
        "next_step": "Matched items se PO create karne ke liye /api/purchase/ use karo"
    }


# ──────────────────────────────────────
# 3. CSV Template Download
# ──────────────────────────────────────
@router.get("/csv-template")
def csv_template(
    current_user: User = Depends(get_current_user)
):
    """CSV template ka format batao — invoice upload ke liye"""

    return {
        "message": "CSV file is format mein banao",
        "required_columns": ["product_name OR barcode", "qty", "unit_price"],
        "optional_columns": ["batch_number", "expiry_date (YYYY-MM-DD)"],
        "example_rows": [
            {"product_name": "Amul Butter 500g", "qty": 50, "unit_price": 230, "batch_number": "B-2026-MAR", "expiry_date": "2026-09-15"},
            {"product_name": "Tata Salt 1kg", "qty": 100, "unit_price": 22, "batch_number": "", "expiry_date": ""},
            {"barcode": "8901030010064", "qty": 30, "unit_price": 230, "batch_number": "B-100", "expiry_date": "2026-12-01"}
        ],
        "notes": [
            "product_name ya barcode mein se ek dena zaroori hai",
            "product_name partial match bhi karta hai (e.g. 'Amul' se 'Amul Butter 500g' match hoga)",
            "expiry_date format: YYYY-MM-DD ya DD-MM-YYYY ya DD/MM/YYYY",
            "CSV encoding: UTF-8 recommended"
        ]
    }


# ──────────────────────────────────────
# 4. Export Sales Data as CSV format
# ──────────────────────────────────────
@router.get("/export-sales")
def export_sales_data(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"]))
):
    """Sales data export — CSV banane ke liye data de do"""

    orders = db.query(Order).filter(
        Order.order_type == "sale",
        func.date(Order.created_at) >= start_date,
        func.date(Order.created_at) <= end_date
    ).order_by(Order.created_at).all()

    export_data = []
    for o in orders:
        items = db.query(OrderItem).filter(OrderItem.order_id == o.id).all()
        for item in items:
            export_data.append({
                "invoice_number": o.invoice_number,
                "date": str(o.created_at.date()) if o.created_at else "",
                "product_name": item.product_name,
                "qty": item.qty,
                "unit_price": item.unit_price,
                "gst_rate": item.gst_rate,
                "gst_amount": item.gst_amount,
                "item_total": item.total,
                "payment_mode": o.payment_mode,
                "bill_total": o.grand_total
            })

    return {
        "period": {"start": str(start_date), "end": str(end_date)},
        "total_records": len(export_data),
        "columns": ["invoice_number", "date", "product_name", "qty", "unit_price", "gst_rate", "gst_amount", "item_total", "payment_mode", "bill_total"],
        "data": export_data
    }

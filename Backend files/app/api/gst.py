# SmartStore ERP — GST + India Law APIs
# Phase 8: GST Calculation, HSN Lookup, GSTR-1/2 Summary, e-Invoice, Compliance

import hashlib
import random
import string
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.gst import GSTConfig, HSNCode, EInvoice
from app.models.order import Order, OrderItem
from app.models.purchase import PurchaseOrder
from app.models.user import User
from app.schemas.gst import (
    GSTConfigCreate, GSTConfigResponse,
    HSNCodeCreate, HSNCodeResponse,
    GSTCalculateRequest, GSTCalculateResponse,
    EInvoiceCreate, EInvoiceResponse,
    GSTR1SummaryResponse, GSTR1LineItem,
    GSTR2SummaryResponse,
    ComplianceResponse, ComplianceItem,
)

router = APIRouter(prefix="/gst", tags=["GST - India Law"])


# ─────────────────────────────────────────────────────────
# HELPER: IRN generate karo (64-char hash like NIC format)
# ─────────────────────────────────────────────────────────
def generate_irn(gstin: str, invoice_number: str, date_str: str) -> str:
    """IRN = SHA-256 hash of GSTIN + InvoiceNo + Date"""
    raw = f"{gstin}{invoice_number}{date_str}"
    return hashlib.sha256(raw.encode()).hexdigest()


def generate_ack_number() -> str:
    """ACK number = 15-digit random number (like NIC portal)"""
    return "".join(random.choices(string.digits, k=15))


# ─────────────────────────────────────────────────────────
# 1. GST CONFIG — Store ka GSTIN setup karo
# ─────────────────────────────────────────────────────────
@router.post("/config", response_model=GSTConfigResponse, status_code=201)
def create_gst_config(
    config: GSTConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Store ka GST config save karo — GSTIN, state, registration"""
    existing = db.query(GSTConfig).first()
    if existing:
        raise HTTPException(status_code=400, detail="GST config already exists. /gst/config PUT se update karo.")

    new_config = GSTConfig(**config.model_dump())
    db.add(new_config)
    db.commit()
    db.refresh(new_config)
    return new_config


@router.put("/config", response_model=GSTConfigResponse)
def update_gst_config(
    config: GSTConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """GST config update karo"""
    existing = db.query(GSTConfig).first()
    if not existing:
        raise HTTPException(status_code=404, detail="GST config nahi mili. Pehle POST /gst/config karo.")

    for key, value in config.model_dump().items():
        setattr(existing, key, value)

    db.commit()
    db.refresh(existing)
    return existing


@router.get("/config", response_model=GSTConfigResponse)
def get_gst_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Store ka current GST config dekho"""
    config = db.query(GSTConfig).first()
    if not config:
        raise HTTPException(status_code=404, detail="GST config nahi mili. Pehle POST /gst/config karo.")
    return config


# ─────────────────────────────────────────────────────────
# 2. HSN CODES — Product HSN se GST rate lookup
# ─────────────────────────────────────────────────────────
@router.post("/hsn", response_model=HSNCodeResponse, status_code=201)
def add_hsn_code(
    hsn: HSNCodeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Naya HSN code add karo with GST rate"""
    existing = db.query(HSNCode).filter(HSNCode.hsn_code == hsn.hsn_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"HSN {hsn.hsn_code} already exists")

    new_hsn = HSNCode(**hsn.model_dump())
    db.add(new_hsn)
    db.commit()
    db.refresh(new_hsn)
    return new_hsn


@router.get("/hsn", response_model=list[HSNCodeResponse])
def list_hsn_codes(
    search: Optional[str] = Query(None, description="HSN code ya description search"),
    category: Optional[str] = Query(None),
    gst_rate: Optional[float] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Saare HSN codes list karo — filter by rate ya category"""
    query = db.query(HSNCode)

    if search:
        query = query.filter(
            (HSNCode.hsn_code.ilike(f"%{search}%")) |
            (HSNCode.description.ilike(f"%{search}%"))
        )
    if category:
        query = query.filter(HSNCode.category.ilike(f"%{category}%"))
    if gst_rate is not None:
        query = query.filter(HSNCode.gst_rate == gst_rate)

    return query.order_by(HSNCode.hsn_code).all()


@router.get("/hsn/{hsn_code}", response_model=HSNCodeResponse)
def get_hsn_code(
    hsn_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ek HSN code ki detail — rate kya hai"""
    hsn = db.query(HSNCode).filter(HSNCode.hsn_code == hsn_code).first()
    if not hsn:
        raise HTTPException(status_code=404, detail=f"HSN code {hsn_code} nahi mila")
    return hsn


# ─────────────────────────────────────────────────────────
# 3. GST CALCULATOR — Amount pe GST nikalo
# ─────────────────────────────────────────────────────────
@router.post("/calculate", response_model=GSTCalculateResponse)
def calculate_gst(payload: GSTCalculateRequest):
    """
    GST calculate karo — CGST+SGST (same state) ya IGST (different state)

    - Intra-state (Maharashtra → Maharashtra): GST splits into CGST + SGST equally
    - Inter-state (Maharashtra → Gujarat): Poora GST = IGST
    """
    amount = round(payload.amount, 2)
    rate = payload.gst_rate
    half_rate = round(rate / 2, 2)

    total_gst = round(amount * rate / 100, 2)
    cess_amount = round(amount * payload.include_cess / 100, 2)

    if payload.is_interstate:
        # IGST only
        return GSTCalculateResponse(
            taxable_amount=amount,
            gst_rate=rate,
            cgst_rate=None,
            sgst_rate=None,
            igst_rate=rate,
            cgst_amount=None,
            sgst_amount=None,
            igst_amount=total_gst,
            cess_amount=cess_amount,
            total_gst=total_gst,
            grand_total=round(amount + total_gst + cess_amount, 2),
            supply_type="Inter-State (IGST)",
        )
    else:
        # CGST + SGST
        cgst = round(amount * half_rate / 100, 2)
        sgst = round(amount * half_rate / 100, 2)
        return GSTCalculateResponse(
            taxable_amount=amount,
            gst_rate=rate,
            cgst_rate=half_rate,
            sgst_rate=half_rate,
            igst_rate=None,
            cgst_amount=cgst,
            sgst_amount=sgst,
            igst_amount=None,
            cess_amount=cess_amount,
            total_gst=total_gst,
            grand_total=round(amount + total_gst + cess_amount, 2),
            supply_type="Intra-State (CGST + SGST)",
        )


# ─────────────────────────────────────────────────────────
# 4. GSTR-1 SUMMARY — Monthly Output Tax (Sales)
# ─────────────────────────────────────────────────────────
@router.get("/gstr1", response_model=GSTR1SummaryResponse)
def gstr1_summary(
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    year: int = Query(..., ge=2020, description="Year (e.g. 2026)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    GSTR-1 Summary — Us month ki saari sales ka GST breakup.
    Ye CA ko bhejne wali report hai.
    """
    orders = db.query(Order).filter(
        Order.order_type == "sale",
        extract("month", Order.created_at) == month,
        extract("year", Order.created_at) == year,
    ).all()

    if not orders:
        return GSTR1SummaryResponse(
            month=month, year=year,
            total_invoices=0, total_taxable_amount=0,
            total_cgst=0, total_sgst=0, total_igst=0,
            total_gst_collected=0, total_sale_amount=0,
            rate_wise_breakup=[],
        )

    # Rate-wise breakup calculate karo using order items
    rate_map: dict = {}

    for order in orders:
        items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        for item in items:
            rate = item.gst_rate or 0.0
            taxable = round(item.unit_price * item.qty, 2)
            gst_amt = item.gst_amount or 0.0
            half_gst = round(gst_amt / 2, 2)

            if rate not in rate_map:
                rate_map[rate] = {
                    "taxable": 0, "cgst": 0, "sgst": 0, "igst": 0, "count": 0
                }
            rate_map[rate]["taxable"] += taxable
            rate_map[rate]["cgst"] += half_gst
            rate_map[rate]["sgst"] += half_gst
            rate_map[rate]["count"] += 1

    rate_wise = []
    for rate, data in rate_map.items():
        total_gst = round(data["cgst"] + data["sgst"], 2)
        rate_wise.append(GSTR1LineItem(
            hsn_code=None,
            gst_rate=rate,
            taxable_amount=round(data["taxable"], 2),
            cgst=round(data["cgst"], 2),
            sgst=round(data["sgst"], 2),
            igst=round(data["igst"], 2),
            total_gst=total_gst,
            invoice_count=data["count"],
        ))

    total_taxable = sum(r.taxable_amount for r in rate_wise)
    total_cgst = sum(r.cgst for r in rate_wise)
    total_sgst = sum(r.sgst for r in rate_wise)
    total_gst = sum(r.total_gst for r in rate_wise)
    total_sale = sum(o.grand_total for o in orders)

    return GSTR1SummaryResponse(
        month=month, year=year,
        total_invoices=len(orders),
        total_taxable_amount=round(total_taxable, 2),
        total_cgst=round(total_cgst, 2),
        total_sgst=round(total_sgst, 2),
        total_igst=0.0,
        total_gst_collected=round(total_gst, 2),
        total_sale_amount=round(total_sale, 2),
        rate_wise_breakup=rate_wise,
    )


# ─────────────────────────────────────────────────────────
# 5. GSTR-2 SUMMARY — Monthly Input Tax Credit (Purchases)
# ─────────────────────────────────────────────────────────
@router.get("/gstr2", response_model=GSTR2SummaryResponse)
def gstr2_summary(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    GSTR-2 Summary — Us month ki saari purchases ka Input Tax Credit.
    Jo GST tumne khareedne pe diya, wo wapas milta hai — ITC.
    """
    pos = db.query(PurchaseOrder).filter(
        PurchaseOrder.status == "received",
        extract("month", PurchaseOrder.created_at) == month,
        extract("year", PurchaseOrder.created_at) == year,
    ).all()

    if not pos:
        return GSTR2SummaryResponse(
            month=month, year=year,
            total_purchase_orders=0,
            total_taxable_amount=0,
            total_cgst_credit=0,
            total_sgst_credit=0,
            total_igst_credit=0,
            total_itc_available=0,
        )

    total_taxable = sum(p.subtotal or 0 for p in pos)
    total_gst = sum(p.gst_amount or 0 for p in pos)
    half_gst = round(total_gst / 2, 2)

    return GSTR2SummaryResponse(
        month=month, year=year,
        total_purchase_orders=len(pos),
        total_taxable_amount=round(total_taxable, 2),
        total_cgst_credit=half_gst,
        total_sgst_credit=half_gst,
        total_igst_credit=0.0,
        total_itc_available=round(total_gst, 2),
    )


# ─────────────────────────────────────────────────────────
# 6. e-INVOICE / IRN GENERATION
# ─────────────────────────────────────────────────────────
@router.post("/einvoice", response_model=EInvoiceResponse, status_code=201)
def generate_einvoice(
    payload: EInvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    e-Invoice generate karo — IRN (Invoice Reference Number) banao.
    Note: Ye simulated IRN hai (real NIC portal ke liye API keys chahiye).
    B2B invoices ke liye buyer ka GSTIN dena zaroori hai.
    """
    # Order check
    order = db.query(Order).filter(Order.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Order ID {payload.order_id} nahi mila")

    # Already generated check
    existing = db.query(EInvoice).filter(EInvoice.order_id == payload.order_id).first()
    if existing and existing.status == "generated":
        raise HTTPException(status_code=400, detail=f"Is order ka IRN already generated hai: {existing.irn}")

    # GST config se GSTIN lo
    config = db.query(GSTConfig).first()
    gstin = config.gstin if config and config.gstin else "UNREGISTERED"

    # IRN generate karo
    date_str = order.created_at.strftime("%Y%m%d")
    irn = generate_irn(gstin, order.invoice_number, date_str)
    ack_no = generate_ack_number()

    einvoice = EInvoice(
        order_id=order.id,
        invoice_number=order.invoice_number,
        irn=irn,
        ack_number=ack_no,
        ack_date=datetime.now(),
        qr_data=f"IRN:{irn}|Invoice:{order.invoice_number}|Date:{date_str}|GSTIN:{gstin}|Amt:{order.grand_total}",
        buyer_gstin=payload.buyer_gstin,
        supply_type=payload.supply_type,
        status="generated",
    )

    db.add(einvoice)
    db.commit()
    db.refresh(einvoice)
    return einvoice


@router.get("/einvoice/{order_id}", response_model=EInvoiceResponse)
def get_einvoice(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Kisi order ka e-Invoice / IRN detail dekho"""
    einvoice = db.query(EInvoice).filter(EInvoice.order_id == order_id).first()
    if not einvoice:
        raise HTTPException(status_code=404, detail=f"Order {order_id} ka e-Invoice nahi mila. Pehle generate karo.")
    return einvoice


@router.delete("/einvoice/{order_id}/cancel")
def cancel_einvoice(
    order_id: int,
    reason: str = Query(..., description="Cancel karne ka reason"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """e-Invoice cancel karo (within 24 hours as per GST rules)"""
    einvoice = db.query(EInvoice).filter(EInvoice.order_id == order_id).first()
    if not einvoice:
        raise HTTPException(status_code=404, detail="e-Invoice nahi mili")
    if einvoice.status == "cancelled":
        raise HTTPException(status_code=400, detail="Ye e-Invoice already cancelled hai")

    einvoice.status = "cancelled"
    einvoice.cancel_reason = reason
    db.commit()
    return {"message": f"e-Invoice {einvoice.irn[:16]}... cancelled", "reason": reason}


# ─────────────────────────────────────────────────────────
# 7. COMPLIANCE CHECKLIST
# ─────────────────────────────────────────────────────────
@router.get("/compliance", response_model=ComplianceResponse)
def compliance_check(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    India Law Compliance Checklist — kya kya zaroori hai, kya missing hai.
    GSTIN, turnover limit, e-invoicing threshold, etc.
    """
    config = db.query(GSTConfig).first()
    checklist = []

    business_name = config.business_name if config else "Unknown"
    gstin = config.gstin if config else None
    annual_turnover = config.annual_turnover if config else 0

    # 1. GST Registration check
    if not config or not config.is_gst_registered:
        if annual_turnover >= 4000000:  # 40 lakh threshold
            checklist.append(ComplianceItem(
                check="GST Registration",
                status="ACTION REQUIRED",
                details=f"Turnover Rs {annual_turnover:,.0f} hai — 40 lakh se zyada. GST registration zaroori hai."
            ))
        else:
            checklist.append(ComplianceItem(
                check="GST Registration",
                status="OK",
                details=f"Turnover Rs {annual_turnover:,.0f} — 40 lakh limit ke andar. Optional hai."
            ))
    else:
        checklist.append(ComplianceItem(
            check="GST Registration",
            status="OK",
            details=f"GSTIN registered: {gstin}"
        ))

    # 2. e-Invoicing threshold (5 crore)
    if annual_turnover >= 50000000:
        checklist.append(ComplianceItem(
            check="e-Invoicing (IRN)",
            status="ACTION REQUIRED",
            details="Turnover 5 crore+ hai — e-Invoice mandatory hai har B2B invoice pe."
        ))
    elif annual_turnover >= 10000000:
        checklist.append(ComplianceItem(
            check="e-Invoicing (IRN)",
            status="WARNING",
            details="Turnover 1-5 crore range mein hai — e-Invoice recommended hai."
        ))
    else:
        checklist.append(ComplianceItem(
            check="e-Invoicing (IRN)",
            status="OK",
            details="Turnover 1 crore se kam — e-Invoice optional hai."
        ))

    # 3. Composition Scheme check
    if config and config.composition_scheme:
        if annual_turnover > 15000000:  # 1.5 crore
            checklist.append(ComplianceItem(
                check="Composition Scheme",
                status="ACTION REQUIRED",
                details="Composition scheme mein ho lekin turnover 1.5 crore+ — regular scheme pe aana padega."
            ))
        else:
            checklist.append(ComplianceItem(
                check="Composition Scheme",
                status="OK",
                details="Composition scheme valid hai (turnover 1.5 crore ke andar)."
            ))

    # 4. GSTR-1 filing (monthly reminder)
    current_month = datetime.now().month
    current_year = datetime.now().year
    month_sales = db.query(Order).filter(
        Order.order_type == "sale",
        extract("month", Order.created_at) == current_month,
        extract("year", Order.created_at) == current_year,
    ).count()

    if month_sales > 0 and config and config.is_gst_registered:
        checklist.append(ComplianceItem(
            check="GSTR-1 Filing",
            status="WARNING",
            details=f"Is month {month_sales} invoices hain — GSTR-1 file karo (11th tak monthly filers ke liye)."
        ))
    else:
        checklist.append(ComplianceItem(
            check="GSTR-1 Filing",
            status="OK",
            details="Is month koi sale nahi ya GST registered nahi."
        ))

    # 5. Professional Tax (Maharashtra)
    if config and config.state_name == "Maharashtra":
        checklist.append(ComplianceItem(
            check="Professional Tax (PT) — Maharashtra",
            status="WARNING",
            details="Maharashtra mein har employee pe PT zaroori hai. Rs 200/mo (salary > 10k). Enrolment certificate lena padega."
        ))

    # 6. HSN Codes on invoices
    hsn_count = db.query(HSNCode).count()
    if hsn_count == 0:
        checklist.append(ComplianceItem(
            check="HSN Codes",
            status="WARNING",
            details="Koi HSN code nahi add kiya. GST invoices pe HSN mandatory hai (turnover 5 crore+ ke liye 6-digit, baaki 4-digit)."
        ))
    else:
        checklist.append(ComplianceItem(
            check="HSN Codes",
            status="OK",
            details=f"{hsn_count} HSN codes registered hain."
        ))

    # Overall status
    statuses = [c.status for c in checklist]
    if "ACTION REQUIRED" in statuses:
        overall = "ACTION REQUIRED"
    elif "WARNING" in statuses:
        overall = "WARNINGS PRESENT"
    else:
        overall = "ALL GOOD"

    return ComplianceResponse(
        business_name=business_name,
        gstin=gstin,
        overall_status=overall,
        checklist=checklist,
    )

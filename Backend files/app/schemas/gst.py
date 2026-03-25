# SmartStore ERP — GST Schemas
# Request/Response formats for GST APIs

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ── GST Config ──────────────────────────────────────────
class GSTConfigCreate(BaseModel):
    business_name: str
    gstin: Optional[str] = None
    state_name: str = "Maharashtra"
    state_code: str = "27"
    is_gst_registered: bool = False
    composition_scheme: bool = False
    annual_turnover: float = 0.0


class GSTConfigResponse(GSTConfigCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── HSN Code ────────────────────────────────────────────
class HSNCodeCreate(BaseModel):
    hsn_code: str
    description: str
    gst_rate: float = Field(ge=0, le=28)
    cess_rate: float = 0.0
    category: Optional[str] = None


class HSNCodeResponse(HSNCodeCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── GST Calculation ─────────────────────────────────────
class GSTCalculateRequest(BaseModel):
    amount: float = Field(gt=0, description="Taxable amount (excluding GST)")
    gst_rate: float = Field(ge=0, le=28, description="GST rate in %")
    is_interstate: bool = Field(default=False, description="True=IGST, False=CGST+SGST")
    include_cess: float = Field(default=0.0, description="Cess % if any")


class GSTCalculateResponse(BaseModel):
    taxable_amount: float
    gst_rate: float
    cgst_rate: Optional[float]
    sgst_rate: Optional[float]
    igst_rate: Optional[float]
    cgst_amount: Optional[float]
    sgst_amount: Optional[float]
    igst_amount: Optional[float]
    cess_amount: float
    total_gst: float
    grand_total: float
    supply_type: str  # "Intra-State" or "Inter-State"


# ── e-Invoice ────────────────────────────────────────────
class EInvoiceCreate(BaseModel):
    order_id: int
    buyer_gstin: Optional[str] = None
    supply_type: str = "B2C"  # B2B / B2C / EXPORT


class EInvoiceResponse(BaseModel):
    id: int
    order_id: int
    invoice_number: str
    irn: Optional[str]
    ack_number: Optional[str]
    ack_date: Optional[datetime]
    qr_data: Optional[str]
    buyer_gstin: Optional[str]
    supply_type: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── GSTR-1 Summary (Output Tax) ─────────────────────────
class GSTR1LineItem(BaseModel):
    hsn_code: Optional[str]
    gst_rate: float
    taxable_amount: float
    cgst: float
    sgst: float
    igst: float
    total_gst: float
    invoice_count: int


class GSTR1SummaryResponse(BaseModel):
    month: int
    year: int
    total_invoices: int
    total_taxable_amount: float
    total_cgst: float
    total_sgst: float
    total_igst: float
    total_gst_collected: float
    total_sale_amount: float
    rate_wise_breakup: List[GSTR1LineItem]


# ── GSTR-2 Summary (Input Tax) ──────────────────────────
class GSTR2SummaryResponse(BaseModel):
    month: int
    year: int
    total_purchase_orders: int
    total_taxable_amount: float
    total_cgst_credit: float
    total_sgst_credit: float
    total_igst_credit: float
    total_itc_available: float


# ── Compliance Checklist ─────────────────────────────────
class ComplianceItem(BaseModel):
    check: str
    status: str   # OK / WARNING / ACTION REQUIRED
    details: str


class ComplianceResponse(BaseModel):
    business_name: str
    gstin: Optional[str]
    overall_status: str
    checklist: List[ComplianceItem]

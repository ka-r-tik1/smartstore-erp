# SmartStore ERP — Staff, Attendance, Payroll Schemas

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date


# ── Staff ───────────────────────────────────────────────
class StaffCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    role: str = "staff"  # owner / cashier / staff / delivery
    salary: float = 0.0
    aadhar_number: Optional[str] = None
    bank_account: Optional[str] = None
    bank_ifsc: Optional[str] = None
    join_date: Optional[date] = None


class StaffUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    salary: Optional[float] = None
    aadhar_number: Optional[str] = None
    bank_account: Optional[str] = None
    bank_ifsc: Optional[str] = None
    is_active: Optional[bool] = None


class StaffResponse(BaseModel):
    id: int
    name: str
    phone: Optional[str]
    email: Optional[str]
    role: str
    salary: float
    aadhar_number: Optional[str]
    bank_account: Optional[str]
    bank_ifsc: Optional[str]
    join_date: Optional[date]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Attendance ──────────────────────────────────────────
class AttendanceMarkRequest(BaseModel):
    staff_id: int
    date: date
    status: str = "present"  # present / absent / half_day / leave
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    overtime_hours: float = 0.0
    notes: Optional[str] = None


class AttendanceResponse(BaseModel):
    id: int
    staff_id: int
    date: date
    status: str
    check_in: Optional[datetime]
    check_out: Optional[datetime]
    hours_worked: float
    overtime_hours: float
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AttendanceSummary(BaseModel):
    staff_id: int
    staff_name: str
    month: int
    year: int
    present: int
    absent: int
    half_days: int
    leaves: int
    total_overtime: float


# ── Payroll ─────────────────────────────────────────────
class PayrollGenerateRequest(BaseModel):
    staff_id: int
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2020)
    total_working_days: int = 30
    overtime_rate_per_hour: float = 50.0   # Rs per OT hour
    bonus: float = 0.0
    deductions: float = 0.0
    deduction_notes: Optional[str] = None


class PayrollResponse(BaseModel):
    id: int
    staff_id: int
    month: int
    year: int
    base_salary: float
    days_present: int
    days_absent: int
    half_days: int
    total_working_days: int
    overtime_hours: float
    overtime_pay: float
    bonus: float
    deductions: float
    deduction_notes: Optional[str]
    net_salary: float
    payment_status: str
    payment_date: Optional[date]
    payment_mode: Optional[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PayrollPayRequest(BaseModel):
    payment_mode: str = "cash"  # cash / upi / bank


class PayrollSummaryResponse(BaseModel):
    month: int
    year: int
    total_staff: int
    total_base_salary: float
    total_overtime_pay: float
    total_bonus: float
    total_deductions: float
    total_net_salary: float
    paid_count: int
    pending_count: int

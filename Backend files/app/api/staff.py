# SmartStore ERP — Staff + Attendance + Payroll APIs
# Phase 9: Staff CRUD, Daily Attendance, Monthly Salary Generation

from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import extract

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.staff import Staff, Attendance, Payroll
from app.models.user import User
from app.schemas.staff import (
    StaffCreate, StaffUpdate, StaffResponse,
    AttendanceMarkRequest, AttendanceResponse, AttendanceSummary,
    PayrollGenerateRequest, PayrollResponse, PayrollPayRequest, PayrollSummaryResponse,
)

router = APIRouter(prefix="/staff", tags=["Staff + Payroll"])


# ─────────────────────────────────────────────────────────
# 1. STAFF CRUD
# ─────────────────────────────────────────────────────────
@router.post("/", response_model=StaffResponse, status_code=201)
def add_staff(
    staff: StaffCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Naya staff member add karo"""
    if staff.email:
        existing = db.query(Staff).filter(Staff.email == staff.email).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Email {staff.email} already registered hai")

    new_staff = Staff(**staff.model_dump())
    db.add(new_staff)
    db.commit()
    db.refresh(new_staff)
    return new_staff


@router.get("/", response_model=list[StaffResponse])
def list_staff(
    role: Optional[str] = Query(None, description="Filter by role: owner/cashier/staff/delivery"),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Saare staff members ki list"""
    query = db.query(Staff)
    if role:
        query = query.filter(Staff.role == role)
    if is_active is not None:
        query = query.filter(Staff.is_active == is_active)
    return query.order_by(Staff.name).all()


@router.get("/{staff_id}", response_model=StaffResponse)
def get_staff(
    staff_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ek staff member ki detail"""
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff nahi mila")
    return staff


@router.put("/{staff_id}", response_model=StaffResponse)
def update_staff(
    staff_id: int,
    data: StaffUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Staff ki info update karo — salary, role, phone etc."""
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff nahi mila")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(staff, key, value)

    db.commit()
    db.refresh(staff)
    return staff


# ─────────────────────────────────────────────────────────
# 2. ATTENDANCE
# ─────────────────────────────────────────────────────────
@router.post("/attendance", response_model=AttendanceResponse, status_code=201)
def mark_attendance(
    data: AttendanceMarkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Daily attendance mark karo — present/absent/half_day/leave"""
    # Staff exists?
    staff = db.query(Staff).filter(Staff.id == data.staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff nahi mila")

    # Already marked?
    existing = db.query(Attendance).filter(
        Attendance.staff_id == data.staff_id,
        Attendance.date == data.date,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Attendance already marked hai {data.date} ke liye")

    # Hours calculate karo
    hours = 0.0
    if data.check_in and data.check_out:
        diff = data.check_out - data.check_in
        hours = round(diff.total_seconds() / 3600, 2)

    if data.status == "half_day":
        hours = min(hours, 4.0) if hours > 0 else 4.0
    elif data.status in ("absent", "leave"):
        hours = 0.0

    attendance = Attendance(
        staff_id=data.staff_id,
        date=data.date,
        status=data.status,
        check_in=data.check_in,
        check_out=data.check_out,
        hours_worked=hours,
        overtime_hours=data.overtime_hours,
        notes=data.notes,
    )

    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance


@router.get("/attendance/daily", response_model=list[AttendanceResponse])
def daily_attendance(
    date: date = Query(..., description="Date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ek din ki saare staff ki attendance"""
    records = db.query(Attendance).filter(Attendance.date == date).all()
    return records


@router.get("/attendance/{staff_id}/monthly", response_model=AttendanceSummary)
def monthly_attendance_summary(
    staff_id: int,
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ek staff ka monthly attendance summary — kitne din aaya, kitne absent"""
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff nahi mila")

    records = db.query(Attendance).filter(
        Attendance.staff_id == staff_id,
        extract("month", Attendance.date) == month,
        extract("year", Attendance.date) == year,
    ).all()

    present = sum(1 for r in records if r.status == "present")
    absent = sum(1 for r in records if r.status == "absent")
    half_days = sum(1 for r in records if r.status == "half_day")
    leaves = sum(1 for r in records if r.status == "leave")
    total_ot = sum(r.overtime_hours for r in records)

    return AttendanceSummary(
        staff_id=staff_id,
        staff_name=staff.name,
        month=month,
        year=year,
        present=present,
        absent=absent,
        half_days=half_days,
        leaves=leaves,
        total_overtime=round(total_ot, 2),
    )


# ─────────────────────────────────────────────────────────
# 3. PAYROLL
# ─────────────────────────────────────────────────────────
@router.post("/payroll/generate", response_model=PayrollResponse, status_code=201)
def generate_payroll(
    data: PayrollGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Monthly salary slip generate karo — attendance se auto calculate.

    Formula:
    - Per day salary = base_salary / total_working_days
    - Effective days = present + (half_days * 0.5)
    - Earned salary = per_day * effective_days
    - Overtime pay = overtime_hours * OT rate
    - Net = earned + overtime + bonus - deductions
    """
    # Staff check
    staff = db.query(Staff).filter(Staff.id == data.staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff nahi mila")

    # Already generated?
    existing = db.query(Payroll).filter(
        Payroll.staff_id == data.staff_id,
        Payroll.month == data.month,
        Payroll.year == data.year,
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"{staff.name} ka {data.month}/{data.year} payroll already generated hai (ID: {existing.id})"
        )

    # Attendance se days nikalo
    records = db.query(Attendance).filter(
        Attendance.staff_id == data.staff_id,
        extract("month", Attendance.date) == data.month,
        extract("year", Attendance.date) == data.year,
    ).all()

    days_present = sum(1 for r in records if r.status == "present")
    days_absent = sum(1 for r in records if r.status == "absent")
    half_days = sum(1 for r in records if r.status == "half_day")
    total_ot = sum(r.overtime_hours for r in records)

    # Salary calculate karo
    base = staff.salary
    per_day = round(base / data.total_working_days, 2) if data.total_working_days > 0 else 0
    effective_days = days_present + (half_days * 0.5)
    earned_salary = round(per_day * effective_days, 2)

    ot_pay = round(total_ot * data.overtime_rate_per_hour, 2)
    net = round(earned_salary + ot_pay + data.bonus - data.deductions, 2)

    payroll = Payroll(
        staff_id=data.staff_id,
        month=data.month,
        year=data.year,
        base_salary=base,
        days_present=days_present,
        days_absent=days_absent,
        half_days=half_days,
        total_working_days=data.total_working_days,
        overtime_hours=round(total_ot, 2),
        overtime_pay=ot_pay,
        bonus=data.bonus,
        deductions=data.deductions,
        deduction_notes=data.deduction_notes,
        net_salary=net,
        notes=f"Earned: Rs {earned_salary} ({effective_days} days x Rs {per_day}/day)",
    )

    db.add(payroll)
    db.commit()
    db.refresh(payroll)
    return payroll


@router.get("/payroll/{staff_id}", response_model=list[PayrollResponse])
def get_staff_payroll(
    staff_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ek staff ke saare payroll slips"""
    records = db.query(Payroll).filter(
        Payroll.staff_id == staff_id
    ).order_by(Payroll.year.desc(), Payroll.month.desc()).all()
    return records


@router.put("/payroll/{payroll_id}/pay", response_model=PayrollResponse)
def mark_salary_paid(
    payroll_id: int,
    data: PayrollPayRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Salary paid mark karo — cash/upi/bank"""
    payroll = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll record nahi mila")
    if payroll.payment_status == "paid":
        raise HTTPException(status_code=400, detail="Ye salary already paid hai")

    payroll.payment_status = "paid"
    payroll.payment_date = date.today()
    payroll.payment_mode = data.payment_mode
    db.commit()
    db.refresh(payroll)
    return payroll


@router.get("/payroll/summary/monthly", response_model=PayrollSummaryResponse)
def monthly_payroll_summary(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Poore month ka payroll summary — kitna paisa gaya total"""
    records = db.query(Payroll).filter(
        Payroll.month == month,
        Payroll.year == year,
    ).all()

    if not records:
        return PayrollSummaryResponse(
            month=month, year=year,
            total_staff=0, total_base_salary=0,
            total_overtime_pay=0, total_bonus=0,
            total_deductions=0, total_net_salary=0,
            paid_count=0, pending_count=0,
        )

    return PayrollSummaryResponse(
        month=month,
        year=year,
        total_staff=len(records),
        total_base_salary=round(sum(r.base_salary for r in records), 2),
        total_overtime_pay=round(sum(r.overtime_pay for r in records), 2),
        total_bonus=round(sum(r.bonus for r in records), 2),
        total_deductions=round(sum(r.deductions for r in records), 2),
        total_net_salary=round(sum(r.net_salary for r in records), 2),
        paid_count=sum(1 for r in records if r.payment_status == "paid"),
        pending_count=sum(1 for r in records if r.payment_status == "pending"),
    )

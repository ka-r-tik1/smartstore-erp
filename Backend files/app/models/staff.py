# SmartStore ERP — Staff, Attendance, Payroll Models
# Phase 9: Staff management, daily attendance, monthly salary

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Date, ForeignKey, Text
from sqlalchemy.sql import func

from app.core.database import Base


class Staff(Base):
    """Staff member — dukaan ka koi bhi employee"""
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(15), nullable=True)
    email = Column(String(100), nullable=True, unique=True)
    role = Column(String(20), default="staff")                    # owner / cashier / staff / delivery
    salary = Column(Float, default=0.0)                           # Monthly salary
    aadhar_number = Column(String(12), nullable=True)             # Aadhar number
    bank_account = Column(String(20), nullable=True)              # Bank account number
    bank_ifsc = Column(String(11), nullable=True)                 # IFSC code
    join_date = Column(Date, nullable=True)                       # Joining date
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Attendance(Base):
    """Daily attendance — kaun aaya, kitne time kaam kiya"""
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    status = Column(String(15), default="present")               # present / absent / half_day / leave
    check_in = Column(DateTime, nullable=True)                   # Kab aaya
    check_out = Column(DateTime, nullable=True)                  # Kab gaya
    hours_worked = Column(Float, default=0.0)                    # Kitne ghante kaam kiya
    overtime_hours = Column(Float, default=0.0)                  # Extra overtime
    notes = Column(String(200), nullable=True)                   # Leave reason etc.
    created_at = Column(DateTime, server_default=func.now())


class Payroll(Base):
    """Monthly payroll — salary + deductions + bonus = net pay"""
    __tablename__ = "payroll"

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False, index=True)
    month = Column(Integer, nullable=False)                      # 1-12
    year = Column(Integer, nullable=False)                       # 2026
    base_salary = Column(Float, default=0.0)                     # Monthly salary from Staff
    days_present = Column(Integer, default=0)                    # Kitne din aaya
    days_absent = Column(Integer, default=0)                     # Kitne din nahi aaya
    half_days = Column(Integer, default=0)                       # Kitne half days
    total_working_days = Column(Integer, default=30)             # Month ke working days
    overtime_hours = Column(Float, default=0.0)                  # Total overtime
    overtime_pay = Column(Float, default=0.0)                    # Overtime ka paisa
    bonus = Column(Float, default=0.0)                           # Festival/performance bonus
    deductions = Column(Float, default=0.0)                      # PF/PT/advance/fine
    deduction_notes = Column(String(200), nullable=True)         # Kya kata
    net_salary = Column(Float, default=0.0)                      # Haath mein kitna aayega
    payment_status = Column(String(15), default="pending")       # pending / paid
    payment_date = Column(Date, nullable=True)                   # Kab diya
    payment_mode = Column(String(15), nullable=True)             # cash / upi / bank
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

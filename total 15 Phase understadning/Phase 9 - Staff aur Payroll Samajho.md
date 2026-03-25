# Phase 9 — Staff + Attendance + Payroll

## Layman mein samjho:

Phase 8 mein GST + India law compliance banaya tha.
**Phase 9 mein 3 cheezein banayein:**
1. **Staff Management** — employee add/edit/list (CRUD)
2. **Attendance** — daily present/absent/half_day mark karo, monthly summary
3. **Payroll** — salary auto-calculate (attendance se), paid/pending track

---

## Part A: Staff CRUD (4 APIs)

| API | Kya karta hai | Example |
|---|---|---|
| **POST /staff/** | Naya staff add karo | "Ramesh Patil, Cashier, Rs 15000" |
| **GET /staff/** | Saare staff ki list | Filter by role/active |
| **GET /staff/{id}** | Ek staff ki detail | Ramesh ki puri info |
| **PUT /staff/{id}** | Staff update karo | Salary badhaao, role change |

### Staff Fields:
- Name, Phone, Email, Role (owner/cashier/staff/delivery)
- Salary, Aadhar Number, Bank Account + IFSC
- Join Date, Active/Inactive

---

## Part B: Attendance (3 APIs)

| API | Kya karta hai | Example |
|---|---|---|
| **POST /staff/attendance** | Attendance mark karo | "Ramesh present, 9am-6pm, 1hr OT" |
| **GET /staff/attendance/daily?date=** | Us din ki saari attendance | March 21 ka record |
| **GET /staff/attendance/{id}/monthly** | Monthly summary | "Present: 22, Absent: 3, Half: 1" |

### Attendance Status:
| Status | Matlab | Hours counted |
|---|---|---|
| present | Full day aaya | Check-in se check-out |
| absent | Nahi aaya | 0 |
| half_day | Aadha din | Max 4 hours |
| leave | Chutti li | 0 |

### Auto-calculation:
- Hours = check_out - check_in (automatically)
- Overtime separately track hota hai

---

## Part C: Payroll (4 APIs)

| API | Kya karta hai | Example |
|---|---|---|
| **POST /staff/payroll/generate** | Salary slip generate | Attendance se auto-calculate |
| **GET /staff/payroll/{staff_id}** | Staff ka payroll history | Saare months ke slips |
| **PUT /staff/payroll/{id}/pay** | Salary paid mark karo | "UPI se diya" |
| **GET /staff/payroll/summary/monthly** | Poore month ka summary | Total salary, paid/pending count |

### Salary Formula:
```
Per Day Salary = Base Salary / Working Days
Effective Days = Present Days + (Half Days × 0.5)
Earned Salary = Per Day × Effective Days
Overtime Pay = OT Hours × OT Rate per Hour
Net Salary = Earned + Overtime + Bonus - Deductions
```

### Example — Ramesh (March 2026):
| Item | Value |
|---|---|
| Base Salary | Rs 16,000/month |
| Working Days | 26 |
| Per Day | Rs 615.38 |
| Present | 2 days + 1 half day = 2.5 effective |
| Earned | Rs 1,538.45 |
| Overtime | 1.5 hrs × Rs 75 = Rs 112.50 |
| Bonus | Rs 500 |
| Deductions (PT) | Rs 200 |
| **Net Salary** | **Rs 1,950.95** |

---

## Test Results:

| Test | Result |
|---|---|
| Add Ramesh (Cashier Rs 15000) | Staff #1 created |
| Add Sunil (Delivery Rs 12000) | Staff #2 created |
| Update Ramesh salary to 16000 | Updated |
| Attendance Ramesh Present (19,20 March) | 9hrs + 9.5hrs, 1.5hr OT |
| Attendance Ramesh Half Day (21 March) | 4hrs, Doctor appointment |
| Attendance Sunil Absent (21 March) | 0hrs, Beemar hai |
| Daily Attendance (21 March) | 2 records — half day + absent |
| Monthly Summary Ramesh | Present:2, Half:1, OT:1.5hrs |
| Generate Payroll Ramesh | Net Rs 1950.95 (2.5 days earned) |
| Generate Payroll Sunil | Net Rs 0 (0 days present) |
| Mark Ramesh Paid (UPI) | Status: paid, Date: 2026-03-21 |
| Monthly Summary | 2 staff, Total: Rs 1950.95, 1 paid 1 pending |

---

## Files:

| File | Kya karta hai |
|---|---|
| `app/models/staff.py` | Staff + Attendance + Payroll tables |
| `app/schemas/staff.py` | Saare request/response formats |
| `app/api/staff.py` | 11 APIs — Staff CRUD, Attendance, Payroll |

---

## Dukaan ki bhasha mein:

> Phase 1-8 = Dukaan ready, billing, stock, khata, PO, payments, GST
> **Phase 9 = Staff ka hisaab — kaun aaya, kitna kaam kiya, kitna paisa dena hai**
>
> Jaise dukaan ka owner har mahine end pe register mein dekhta hai ki kaun kitne din aaya, overtime kiya, aur kitni salary deni hai — wahi kaam ye system automatically karta hai. Attendance mark karo, salary slip apne aap ban jayegi.

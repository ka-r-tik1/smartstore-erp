# Phase 5 — Dealers & Udhaar (Credit/Khata System)

## Layman mein samjho:

Phase 4 mein godown ka register banaya tha.
**Phase 5 mein dealers/customers ka khata system banaya — kaun kitna udhaar liya, kab diya, kitna baaki.**

---

## Kya bana Phase 5 mein?

### 8 APIs banaye:

| API | Kya karta hai | Example |
|---|---|---|
| **Add Dealer** | Naya dealer/customer add karo | "Sharma General Store, 9876543210, credit limit Rs 5000" |
| **List Dealers** | Search + filter (udhaar wale, supplier, customer) | "Sirf udhaar wale dikhao" → 4 dealers |
| **Dealer Detail** | Ek dealer ki full info | Name, phone, outstanding, credit limit |
| **Update Dealer** | Credit limit badhao, phone change karo | Sharma ka limit 5000 → 8000 |
| **Collect Payment** | Udhaar ka paisa vasool karo | "Sharma ne Rs 500 UPI se diya" → Outstanding 1340 → 840 |
| **Payment History** | Kab kitna diya — full log | "Rs 500 via UPI, collected by owner1" |
| **Dealer Orders** | Khata — saare orders dekho | "INV-2026-0003, Rs 140, udhaar, pending" |
| **Outstanding Summary** | Sabka total udhaar overview | "Total Rs 14,500 baaki, 4 dealers, top defaulter: Gupta Wholesale" |

---

## Smart Features:

| Feature | Kya karta hai |
|---|---|
| **Credit Limit Check** | Udhaar bill pe limit cross hone se rokta hai |
| **Auto Outstanding Update** | POS mein udhaar bill → dealer ka outstanding auto badhta hai |
| **Payment → Outstanding Minus** | Payment collect karo → outstanding auto ghatta hai |
| **Phone Duplicate Check** | Same phone se 2 dealers nahi ban sakte |
| **Top Defaulters** | Sabse zyada udhaar wale pehle dikhte hain |

---

## Demo Data — 8 Dealers:

| Dealer | Type | Outstanding | Limit |
|---|---|---|---|
| Sharma General Store | Customer | Rs 1,200 | Rs 5,000 |
| Patel Kirana | Customer | Rs 3,500 | Rs 10,000 |
| Gupta Wholesale | Both | Rs 8,000 | Rs 20,000 |
| Rajesh Pan Corner | Customer | Rs 1,800 | Rs 2,000 |
| Amul Distributor | Supplier | Rs 0 | Rs 50,000 |
| Others (3) | Supplier/Customer | Rs 0 | Various |

---

## Test Results:

| Test | Result |
|---|---|
| List Dealers | 8 dealers dikhaye |
| Search "Sharma" | 1 result |
| Udhaar filter | 4 dealers with outstanding > 0 |
| Outstanding Summary | Rs 14,500 total, 4 dealers |
| Udhaar Bill (Sharma, Tata Salt x5) | INV-2026-0003, Rs 140, outstanding 1200 → 1340 |
| Collect Rs 500 UPI | Outstanding 1340 → 840 |
| Payment History | 1 entry with before/after log |
| Dealer Orders (khata) | 1 pending order |

---

## Files:

| File | Kya karta hai |
|---|---|
| `app/schemas/dealer.py` | Dealer + Payment data formats |
| `app/models/payment.py` | Payment collection log table |
| `app/api/dealers.py` | 8 Dealer + Udhaar APIs |
| `seed_dealers.py` | 8 demo dealers |
| `app/api/pos.py` (updated) | Udhaar bill pe dealer outstanding auto-update + credit limit check |

---

## Dukaan ki bhasha mein:

> Phase 1 = Dukaan ka structure
> Phase 2 = Taala (login)
> Phase 3 = Samaan + Billing
> Phase 4 = Godown register
> **Phase 5 = Khata system — kaun kitna udhaar liya, kab diya, kitna baaki**

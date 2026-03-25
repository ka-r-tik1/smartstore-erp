# Phase 6 — Orders + Purchase Orders

## Layman mein samjho:

Phase 5 mein khata system banaya tha (dealers + udhaar).
**Phase 6 mein 2 cheezein banayein:**
1. **Orders management** — saare bills ek jagah dekho, filter karo, cancel karo
2. **Purchase Orders** — supplier ko maal ka order do, approve karo, maal receive karo

---

## Part A: Orders Management (5 APIs)

| API | Kya karta hai | Example |
|---|---|---|
| **List Orders** | Saare orders filter ke saath | "Sirf udhaar wale dikhao" / "March ke orders" |
| **Order Detail** | Ek order ki full detail | Invoice items, GST, payment info |
| **Search by Invoice** | Invoice number se dhundho | "INV-2026-0001" |
| **Cancel Order** | Order cancel — stock wapas, outstanding minus | Sharma ka udhaar cancel → stock restore |
| **Orders Summary** | Revenue, avg bill, payment breakup | "3 orders, Rs 982, avg Rs 327" |

### Cancel ke time kya hota hai:
- Stock wapas aata hai (products mein)
- Agar udhaar tha toh dealer ka outstanding bhi minus hota hai
- Order type "cancelled" ho jaata hai

---

## Part B: Purchase Orders (6 APIs)

| API | Kya karta hai | Example |
|---|---|---|
| **Create PO** | Supplier ko order banao (draft) | "Amul Distributor se 200 Butter + 100 Milk" |
| **List POs** | Saare POs filter ke saath | draft / approved / received |
| **PO Detail** | Full PO with items | Items, qty ordered vs received |
| **Approve PO** | Owner approve kare tab hi receive ho | "PO-2026-0001 approved by owner1" |
| **Receive Goods** | Maal aaya — stock auto-update + batch create | Partial bhi ho sakta hai |
| **Cancel PO** | PO cancel karo | Received PO cancel nahi hota |

### PO Flow:
```
Draft → Approve (Owner) → Receive Goods → Done
                        → Partial Receive → Receive Remaining → Done
```

### Receive ke time kya hota hai:
- Product ka stock automatically badhta hai
- Stock movement log banta hai (audit trail)
- Batch + expiry date record hota hai
- Partial receive supported — baaki baad mein le sakte ho

---

## Test Results:

| Test | Result |
|---|---|
| All Orders List | 3 orders dikhaye |
| Orders Summary | Rs 982 revenue, avg Rs 327 |
| Create PO (Amul — 200 Butter + 100 Milk) | PO-2026-0001, Rs 57,200, draft |
| Approve PO | Approved by owner1 |
| Receive Goods (200 Butter + 100 Milk) | Stock auto-updated, batches created |
| PO Status | "received" — 200/200 + 100/100 |
| Cancel Order (Sharma udhaar) | Stock restored, outstanding Rs 840 → Rs 700 |

---

## Files:

| File | Kya karta hai |
|---|---|
| `app/models/purchase.py` | PurchaseOrder + PurchaseOrderItem tables |
| `app/schemas/purchase.py` | PO data formats (create, receive, response) |
| `app/api/orders.py` | 5 Orders APIs (list, detail, search, cancel, summary) |
| `app/api/purchase.py` | 6 Purchase Order APIs (create, list, detail, approve, receive, cancel) |

---

## Dukaan ki bhasha mein:

> Phase 1 = Dukaan ka structure
> Phase 2 = Taala (login)
> Phase 3 = Samaan + Billing
> Phase 4 = Godown register
> Phase 5 = Khata system
> **Phase 6 = Order tracking + Supplier se maal mangwao (PO system)**

# Phase 4 — Inventory Management

## Layman mein samjho:

Phase 3 mein samaan bhara aur billing machine lagayi thi.
**Phase 4 mein godown ka register banaya — kab maal aaya, kab gaya, kab expire hoga, kitna bacha.**

---

## Kya bana Phase 4 mein?

### 7 APIs banaye:

| API | Kya karta hai | Example |
|---|---|---|
| **Stock In** | Naya maal aaya — batch + expiry ke saath record karo | "100 Amul Butter aaye, Batch B001, Expiry Jun 2026" |
| **Stock Out** | Maal damage/wastage se gaya — record karo | "5 Parle-G baarish mein bheeg gaye" |
| **Movement History** | Kab kya hua — full log | "+100 purchase, -5 damage, -2 sale" |
| **Low Stock Alerts** | Reorder level se neeche wale products | "Britannia Bread sirf 25 bacha, 8 chahiye" |
| **Expiry Alerts** | Jaldi expire hone wale batches | "Maggi Batch MG-202 — 20 din mein expire, 50 pcs bacha" |
| **Batches** | Ek product ke saare batches dekho | "Amul Butter — B001: 100 pcs, Expiry Jun 2026" |
| **Inventory Summary** | Full godown ka overview | "20 products, Rs 1,30,076 retail value, Rs 15,691 profit potential" |

---

## 2 Naye Database Tables:

| Table | Kya store karta hai |
|---|---|
| **stock_movements** | Har stock change ka log — kab, kitna, kyun, kisne |
| **stock_batches** | Batch-wise stock — batch number, expiry date, qty |

---

## Test Results:

| Test | Result |
|---|---|
| Stock In (Amul Butter 100, Batch B001) | 58 -> 158, logged |
| Stock In (Maggi 50, near expiry Apr 10) | 215 -> 265, batch created |
| Stock Out (5 Parle-G damaged) | 145 -> 140, reason logged |
| Movement History | 3 entries dikhaye |
| Expiry Alert (30 days) | Maggi MG-202 — 20 days left |
| Batches (Amul Butter) | B001: 100 pcs, Expiry 2026-06-15 |
| Summary | 20 products, Rs 1,30,076 value |

---

## Files banaye Phase 4 mein:

| File | Kya karta hai |
|---|---|
| `app/models/inventory.py` | StockMovement + StockBatch tables |
| `app/schemas/inventory.py` | Data formats (stock in/out, alerts, batch) |
| `app/api/inventory.py` | 7 Inventory APIs |

---

## Dukaan ki bhasha mein:

> Phase 1 = Dukaan ka structure
> Phase 2 = Taala (login)
> Phase 3 = Samaan + Billing machine
> **Phase 4 = Godown register — maal ka hisaab, expiry tracking, low stock alert**

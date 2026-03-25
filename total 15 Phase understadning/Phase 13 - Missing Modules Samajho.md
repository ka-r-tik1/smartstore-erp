# Phase 13 — 6 Missing Modules Samajho

## Ye Phase Kya Karta Hai?
6 important modules jo pehle nahi the:
1. **Sales Returns** — Customer ne product wapas kiya
2. **Purchase Returns** — Supplier ko maal wapas bheja
3. **GRN** — Goods Received Note (maal aane ka formal record)
4. **Damage & Wastage** — Kharab/expired/lost stock write-off
5. **Stock Transfer** — Ek location se doosri location pe stock move
6. **Smart Alerts** — Low stock, expiry, udhaar due — sab ek jagah

---

## 1. SALES RETURNS — Customer Wapas Kare

### Real Life Example:
```
Customer ne Amul Butter kharida → ghar jaake dekha expire ho gaya
→ wapas aaya → hum return banate hain → stock wapas aata hai → refund milta hai
```

### Flow:
```
Return banao → Approve karo → Stock wapas (good condition only) → Refund
```

### Condition Types:
| Condition | Stock Wapas? |
|---|---|
| good | ✅ Haan |
| damaged | ❌ Nahi |
| expired | ❌ Nahi |

### Refund Modes: cash / credit_note / upi

### 4 APIs:
| # | API | Kya karta hai |
|---|---|---|
| 1 | POST /returns/sales | Return banao |
| 2 | POST /returns/sales/{id}/approve | Approve karo — stock restore |
| 3 | GET /returns/sales | List dekho |
| 4 | GET /returns/sales/{id} | Detail dekho |

### Return Number Format: `SR-2026-0001`

---

## 2. PURCHASE RETURNS — Supplier Ko Wapas

### Real Life Example:
```
Supplier ne damage maal bheja → hum wapas karte hain
→ Purchase Return banate hain → Debit Note milti hai → stock minus hota hai
```

### Flow:
```
Return banao → Send karo → Stock minus → Debit Note auto-generate
```

### Debit Note:
- Automatically banti hai: `DN-PR-2026-0001`
- Supplier ko ye note bhejte hain — unka amount adjust hota hai

### 3 APIs:
| # | API | Kya karta hai |
|---|---|---|
| 1 | POST /returns/purchase | Return banao |
| 2 | POST /returns/purchase/{id}/send | Send karo — stock minus + debit note |
| 3 | GET /returns/purchase | List dekho |

### Return Number Format: `PR-2026-0001`

---

## 3. GRN — Goods Received Note

### GRN Kya Hota Hai?
Jab bhi supplier se maal aata hai — sirf stock update karna kaafi nahi.
GRN ek **formal document** hai jo batata hai:
- Kitna maal order kiya tha
- Kitna actually aaya
- Quality check hua?
- Kitna accept kiya, kitna reject kiya

### Flow:
```
Maal aaya → GRN banao (draft) → Quality check → Verify karo → Stock auto-update
```

### GRN vs PO:
```
PO = "Ye maal chahiye" (order)
GRN = "Ye maal aaya" (receipt)
```

### Qty Breakdown:
```
qty_ordered  = PO mein 100 tha
qty_received = Actually 95 aaya
qty_accepted = Quality pass 90
qty_rejected = 5 reject hua (damaged/wrong batch)
```

### 4 APIs:
| # | API | Kya karta hai |
|---|---|---|
| 1 | POST /grn | GRN banao (draft) |
| 2 | POST /grn/{id}/verify | Verify → stock update |
| 3 | GET /grn | List dekho |
| 4 | GET /grn/{id} | Detail dekho |

### GRN Number Format: `GRN-2026-0001`

---

## 4. DAMAGE & WASTAGE — Nuksaan Ka Record

### 4 Types:
| Type | Matlab |
|---|---|
| damaged | Product toot gaya / kharab hua |
| expired | Expiry nikal gayi |
| lost | Maal gum ho gaya |
| stolen | Chori ho gayi |

### Kya Hota Hai Entry Se:
- Stock **automatically minus** hota hai
- Loss value calculate hoti hai (qty × cost price)
- P&L report mein **expense** dikhega

### Example:
```
10 Amul Butter expire ho gaye
Cost price = Rs 230 each
Loss = 10 × 230 = Rs 2,300 — ye loss dikhega reports mein
```

### 3 APIs:
| # | API | Kya karta hai |
|---|---|---|
| 1 | POST /damage | Damage record karo |
| 2 | GET /damage | List dekho |
| 3 | GET /damage/report | Summary report (type-wise, product-wise) |

### Entry Number Format: `DMG-2026-0001`

---

## 5. STOCK TRANSFER — Location Pe Location

### Use Cases:
- Godown → Shop
- Shop A → Shop B
- Counter → Storage Room

### 3-Step Flow:
```
Step 1: Create Request (pending)
         ↓
Step 2: Dispatch (source se stock minus, status = in_transit)
         ↓
Step 3: Receive (destination pe stock plus, status = received)
```

### Why 3 Steps?
Agar directly ek step mein karo — toh "in transit" stock track nahi hota.
3 steps se pata chalta hai: maal kahan hai abhi.

### 4 APIs:
| # | API | Kya karta hai |
|---|---|---|
| 1 | POST /stock-transfer | Request banao |
| 2 | POST /stock-transfer/{id}/dispatch | Dispatch karo |
| 3 | POST /stock-transfer/{id}/receive | Receive karo |
| 4 | GET /stock-transfer | List dekho |

### Transfer Number Format: `ST-2026-0001`

---

## 6. SMART ALERTS — Business Ki Pulse

### 4 Alert APIs:

| # | API | Kya batata hai |
|---|---|---|
| 1 | GET /alerts/low-stock | Stock reorder level se neeche |
| 2 | GET /alerts/expiry | Products expiring soon |
| 3 | GET /alerts/payment-due | Udhaar collect/pay karna hai |
| 4 | GET /alerts/dashboard | Sab kuch ek jagah |

### Low Stock — 3 Levels:
```
Out of Stock  → Stock = 0
Critical      → Stock ≤ 25% of reorder level
Low           → Stock ≤ reorder level
```

### Expiry Alerts:
```
Already Expired     → Turant action chahiye
Expiring This Week  → 7 din mein
Expiring Soon       → 30 din mein (ya jo bhi set karo)
```

### Dashboard Alert Types:
```
CRITICAL  → Out of stock products (immediate action)
URGENT    → Already expired batches
WARNING   → Low stock products
INFO      → Expiring soon, udhaar due, pending POs
```

### Dashboard Example Response:
```json
{
  "business_pulse": {
    "today_orders": 15,
    "today_revenue": 4500,
    "total_receivable": 12000,
    "total_payable": 3500
  },
  "alerts": [
    {"type": "CRITICAL", "message": "3 products OUT OF STOCK!"},
    {"type": "WARNING",  "message": "8 products low stock"},
    {"type": "INFO",     "message": "Rs 12000 udhaar vasool karna hai"}
  ]
}
```

---

## Sab Files:

| File | Kya hai |
|---|---|
| `app/models/returns.py` | Sales + Purchase Return tables |
| `app/models/grn.py` | GRN table |
| `app/models/damage.py` | Damage & Wastage table |
| `app/models/stock_transfer.py` | Stock Transfer table |
| `app/api/returns.py` | 7 Return APIs |
| `app/api/grn.py` | 4 GRN APIs |
| `app/api/damage.py` | 3 Damage APIs |
| `app/api/stock_transfer.py` | 4 Transfer APIs |
| `app/api/alerts.py` | 4 Alert APIs |
| `main.py` | 5 routers + 4 model imports added |

## Total APIs: 22 endpoints

---

## Quick Test Commands:

```bash
# Dashboard alerts
curl -H "Authorization: Bearer TOKEN" http://localhost:8000/api/alerts/dashboard

# Low stock check
curl -H "Authorization: Bearer TOKEN" http://localhost:8000/api/alerts/low-stock

# Expiry check (30 din)
curl -H "Authorization: Bearer TOKEN" http://localhost:8000/api/alerts/expiry?days_ahead=30

# Sales return banao
curl -X POST http://localhost:8000/api/returns/sales \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"return_date":"2026-03-21","reason":"Expired product","refund_mode":"cash","items":[{"product_id":1,"qty_returned":2,"unit_price":50}]}'
```

---

*Phase 13 Complete — 2026-03-21*

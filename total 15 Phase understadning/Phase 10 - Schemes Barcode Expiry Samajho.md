# Phase 10 — Schemes, Barcode aur Expiry Samajho

## Ye Phase Kya Karta Hai?
Dukaan mein 3 important features add kiye:
1. **Schemes/Offers** — Customer ko discount/offer dena (Buy 1 Get 1, % off, flat off)
2. **Barcode** — Product pe barcode lagao, scan karo, bill mein add ho
3. **Expiry Tracking** — Phase 4 mein already bana tha, yahan confirm kiya

---

## 1. SCHEMES/OFFERS — Kaise Kaam Karta Hai?

### Scheme Types (4 types):
| Type | Matlab | Example |
|------|--------|---------|
| `percent_off` | X% discount | "10% off on everything" |
| `flat_off` | Rs X off | "Rs 50 off on Tata products" |
| `buy_x_get_y` | Buy X Get Y Free | "Buy 2 Get 1 Free Dairy" |
| `combo` | Combo deal | Future use |

### Scheme Applicability (kis pe lagega):
| apply_on | Matlab |
|----------|--------|
| `all` | Sabhi products pe |
| `category` | Ek category pe (Dairy, Snacks) |
| `brand` | Ek brand pe (Amul, Tata) |
| `product` | Specific product IDs pe |

### POS Billing Mein Auto-Apply:
- Jab bill banao, system **automatically** active schemes check karta hai
- Agar ek product pe 2 schemes lag sakti hain, toh **best discount** (highest) apply hota hai
- Manual discount + Scheme discount dono alag calculate hote hain

### Example:
```
Amul Butter ₹280 x 3 = ₹840 (subtotal)
Scheme 1: 10% off = ₹84 discount
Scheme 2: Buy 2 Get 1 = ₹280 discount  ← BEST, ye lagega!
GST 5% = ₹42
Grand Total = ₹840 + ₹42 - ₹280 = ₹602
```

---

## 2. BARCODE — Kaise Kaam Karta Hai?

### Barcode Format:
- **EAN-13** — 13 digit number (international standard)
- Prefix: `890` = India country code
- Remaining digits: product ID + check digit

### Flow:
```
Product Add → Barcode Generate (EAN-13) → Barcode Scan → Product Detail → Bill Mein Add
```

### APIs:
| API | Kya karta hai |
|-----|--------------|
| `POST /barcode/generate/{id}` | Ek product ka barcode banao |
| `POST /barcode/generate-bulk` | Sabhi bina-barcode products ka ek saath |
| `GET /barcode/scan/{barcode}` | Scan karo → product detail milega |
| `GET /barcode/missing` | Konse products pe barcode nahi hai |

---

## 3. EXPIRY TRACKING — Phase 4 Se Hai

Ye Phase 4 (Inventory) mein already bana tha:
- `StockBatch` table mein `expiry_date` field
- `GET /inventory/expiry-alerts?days=30` — next 30 din mein expire hone wale batches
- `GET /inventory/batches/{product_id}` — product ke saare batches with expiry

Phase 10 mein confirm kiya ki ye sahi kaam kar raha hai.

---

## Files Banaye/Change Kiye:

### New Files (4):
| File | Kya hai |
|------|---------|
| `app/models/scheme.py` | Scheme table — offers store karta hai |
| `app/schemas/scheme.py` | Scheme ka input/output format |
| `app/api/schemes.py` | 7 Scheme APIs |
| `app/api/barcode.py` | 4 Barcode APIs |

### Modified Files (2):
| File | Kya change kiya |
|------|----------------|
| `main.py` | schemes_router + barcode_router register kiya |
| `app/api/pos.py` | Bill mein scheme auto-apply logic add kiya |

---

## Total APIs: 13 endpoints

| # | Endpoint | Method | Kya karta hai |
|---|----------|--------|--------------|
| 1 | `/api/schemes/` | POST | Naya scheme banao |
| 2 | `/api/schemes/` | GET | Saare schemes list |
| 3 | `/api/schemes/{id}` | GET | Ek scheme ki detail |
| 4 | `/api/schemes/{id}` | PUT | Scheme update |
| 5 | `/api/schemes/{id}` | DELETE | Scheme deactivate |
| 6 | `/api/schemes/check/{product_id}` | GET | Product pe kaunse schemes lagenge |
| 7 | `/api/schemes/report/summary` | GET | Scheme summary report |
| 8 | `/api/barcode/generate/{id}` | POST | Barcode generate |
| 9 | `/api/barcode/scan/{barcode}` | GET | Barcode scan → product |
| 10 | `/api/barcode/generate-bulk` | POST | Bulk barcode generate |
| 11 | `/api/barcode/missing` | GET | Bina barcode wale products |
| 12 | `/api/inventory/expiry-alerts` | GET | Expiry alerts (Phase 4) |
| 13 | `/api/pos/bill` | POST | Enhanced — scheme auto-apply |

---

## Samajhne Ke Liye Key Points:

1. **Scheme = Dukaan ka offer** — owner create karta hai, system auto-apply karta hai
2. **Barcode = Product ki pehchan** — scan karo, product mil jayega, billing fast hogi
3. **Expiry = Product ki zindagi** — near-expiry alert se pehle bech do, waste mat karo
4. **Best discount auto-select** — agar 2 schemes lag sakti hain, system sabse badi discount lagata hai
5. **Date range** — har scheme ki start/end date hoti hai, expired schemes auto-inactive

---

*Phase 10 Complete — 2026-03-21*

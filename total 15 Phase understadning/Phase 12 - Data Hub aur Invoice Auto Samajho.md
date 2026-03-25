# Phase 12 — Data Hub aur Invoice Auto Samajho

## Ye Phase Kya Karta Hai?
2 bade features:
1. **Data Hub** — Poore business ke reports ek jagah (Sales, Purchase, P&L, Tax, Category, Payment)
2. **Invoice Auto** — Purchase invoice CSV upload karo, auto PO + stock update

---

## 1. DATA HUB — Centralized Reports

### 7 Report APIs:

| # | Report | Kya dikhata hai |
|---|--------|----------------|
| 1 | Sales Report | Date range mein kitni sale, daily/weekly/monthly |
| 2 | Purchase Report | Kitna maal khareeda, supplier wise |
| 3 | Profit & Loss | Revenue - COGS - Expenses = Net Profit |
| 4 | Tax Report | Output GST - Input GST = Net Payable |
| 5 | Category Analysis | Kaunsi category sabse zyada biki |
| 6 | Payment Analysis | Cash/UPI/Card/Udhaar breakup |
| 7 | Business Dashboard | Ek screen pe aaj/week/month summary |

### Profit & Loss samajho:
```
Revenue (Sales)          = ₹1,444
- COGS (Cost of Goods)   = ₹1,485
= Gross Profit           = ₹-40
- Payroll                 = ₹1,951
= Net Profit             = ₹-1,991
```

### Tax Report samajho:
```
Output GST (sale pe collected)   = ₹100
- Input GST (purchase pe paid)   = ₹2,600
= Net GST Payable                = ₹-2,499 (refund milega)
```

---

## 2. INVOICE AUTO — CSV Upload se Auto PO

### Flow:
```
Supplier ka invoice (CSV file) → Upload → Products auto-match → PO create → Stock auto-update → Batch/Expiry save
```

### CSV Format:
```csv
product_name,qty,unit_price,batch_number,expiry_date
Amul Butter,25,230,B-MAR26,2026-09-30
Tata Salt,50,22,,
Maggi,100,10,MG-500,2026-08-15
```

### 4 Invoice APIs:

| # | API | Kya karta hai |
|---|-----|--------------|
| 1 | Upload CSV | CSV upload → auto PO + stock |
| 2 | Parse Text | Text paste karo → products match |
| 3 | CSV Template | Template format batao |
| 4 | Export Sales | Sales data export |

### Smart Features:
- Product name partial match (e.g. "Amul" → "Amul Butter 500g")
- Barcode se bhi match hota hai
- Multiple date formats supported (YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY)
- Errors report karta hai (kaunsi row fail hui, kyun)

---

## Files:

| File | Kya hai |
|------|---------|
| `app/api/data_hub.py` | 7 Report APIs |
| `app/api/invoice_auto.py` | 4 Invoice Auto APIs |
| `main.py` | 2 routers register |

## Total APIs: 11 endpoints

---

*Phase 12 Complete — 2026-03-21*

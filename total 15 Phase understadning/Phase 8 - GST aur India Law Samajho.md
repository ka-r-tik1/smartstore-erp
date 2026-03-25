# Phase 8 — GST + India Law

## Layman mein samjho:

Phase 7 mein payment ledger + bank reconciliation banaya tha.
**Phase 8 mein 5 cheezein banayein:**
1. **GST Config** — store ka GSTIN aur state setup
2. **HSN Code Lookup** — har product ka HSN code aur GST rate
3. **GST Calculator** — same state (CGST+SGST) ya different state (IGST)
4. **GSTR-1 / GSTR-2 Summary** — CA ko bhejne wali monthly report
5. **e-Invoice IRN** — government ka Invoice Reference Number
6. **Compliance Checklist** — kya kya zaroori hai India law ke hisaab se

---

## Part A: GST Config (3 APIs)

| API | Kya karta hai | Example |
|---|---|---|
| **POST /gst/config** | Store ka GSTIN save karo | "27AABCS1429B1Z1, Maharashtra" |
| **PUT /gst/config** | Config update karo | Turnover change karo |
| **GET /gst/config** | Current config dekho | GSTIN, state, registered ya nahi |

---

## Part B: HSN Codes (3 APIs)

HSN = Harmonized System of Nomenclature — har product ka ek code hota hai jisse GST rate pata chalta hai.

| API | Kya karta hai | Example |
|---|---|---|
| **POST /gst/hsn** | Naya HSN code add karo | "1901 - Biscuits - 18%" |
| **GET /gst/hsn** | Saare HSN codes list | Search by code ya description |
| **GET /gst/hsn/{code}** | Ek HSN ki detail | "1901 ka rate kya hai?" |

### Common FMCG HSN + GST Rates:
| HSN | Product | GST Rate |
|---|---|---|
| 0402 | Milk powder | 5% |
| 1806 | Chocolate | 28% |
| 1902 | Noodles/Pasta | 12% |
| 2106 | Food supplements | 18% |
| 3304 | Cosmetics | 28% |
| 0% | Fresh fruits/veg, milk, bread | 0% |

---

## Part C: GST Calculator (1 API)

| Supply Type | Matlab | Formula |
|---|---|---|
| **Intra-State** | Same state mein sale (Maharashtra → Maharashtra) | CGST + SGST (half-half) |
| **Inter-State** | Different state mein sale (Maharashtra → Gujarat) | IGST (poora) |

### Example — Rs 1000 pe 18% GST:
| | Intra-State | Inter-State |
|---|---|---|
| CGST | Rs 90 (9%) | — |
| SGST | Rs 90 (9%) | — |
| IGST | — | Rs 180 (18%) |
| **Total GST** | **Rs 180** | **Rs 180** |
| **Grand Total** | **Rs 1180** | **Rs 1180** |

---

## Part D: GSTR-1 + GSTR-2 (2 APIs)

| API | Kya hai | Kisko bhejo |
|---|---|---|
| **GET /gst/gstr1** | Monthly sales ka GST breakup (output tax) | CA ko / GST portal pe |
| **GET /gst/gstr2** | Monthly purchases ka ITC (input tax credit) | CA ko / GST portal pe |

### GSTR-1 kya hota hai?
> Jo GST tumne customers se collect kiya — wo government ko dena hota hai. GSTR-1 us ka record hai.

### GSTR-2 / ITC kya hota hai?
> Jo GST tumne suppliers ko diya khareedne pe — wo wapas milta hai. Isse Input Tax Credit (ITC) kehte hain.
> **Final Tax = Output GST (GSTR-1) - Input GST (GSTR-2)**

---

## Part E: e-Invoice / IRN (3 APIs)

IRN = Invoice Reference Number — government ka unique stamp har invoice pe.

| API | Kya karta hai |
|---|---|
| **POST /gst/einvoice** | Order ka IRN generate karo |
| **GET /gst/einvoice/{order_id}** | IRN detail + QR data dekho |
| **DELETE /gst/einvoice/{id}/cancel** | IRN cancel karo (24 hours mein) |

### IRN kab zaroori hai?
| Turnover | e-Invoice |
|---|---|
| < 1 Crore | Optional |
| 1-5 Crore | Recommended |
| 5 Crore+ | **Mandatory** |

> Note: Abhi IRN simulated hai (SHA-256 hash). Real IRN ke liye NIC portal ke API keys chahiye honge (Phase 15 deploy ke time).

---

## Part F: Compliance Checklist (1 API)

**GET /gst/compliance** — ek baar call karo, saari India law checklist mil jaayegi:

| Check | Kya dekhta hai |
|---|---|
| GST Registration | Turnover 40 lakh+ hai toh mandatory |
| e-Invoicing | Turnover 5 crore+ hai toh mandatory |
| Composition Scheme | 1.5 crore se zyada hue toh regular pe aao |
| GSTR-1 Filing | Is month ke bills file kiye ya nahi |
| Professional Tax (PT) | Maharashtra mein Rs 200/mo per employee |
| HSN Codes | Add kiye hain ya nahi |

---

## Test Results:

| Test | Result |
|---|---|
| GST Config (GSTIN set) | SmartStore FMCG, Maharashtra registered |
| GST Calculate (Rs 1000, 18%, intra) | CGST Rs 90 + SGST Rs 90 = Rs 1180 |
| GST Calculate (Rs 1000, 18%, inter) | IGST Rs 180 = Rs 1180 |
| GSTR-1 (March 2026) | 2 invoices, Rs 794 taxable, Rs 58.8 GST collected |
| Compliance Check | WARNINGS: GSTR-1 filing, PT, HSN codes |

---

## Files:

| File | Kya karta hai |
|---|---|
| `app/models/gst.py` | GSTConfig + HSNCode + EInvoice tables |
| `app/schemas/gst.py` | Saare request/response formats |
| `app/api/gst.py` | 13 APIs — config, HSN, calculator, GSTR, IRN, compliance |

---

## Dukaan ki bhasha mein:

> Phase 1-7 = Dukaan ready, billing, stock, khata, PO, payments
> **Phase 8 = CA ka kaam aur government ka hisaab**
>
> Jaise dukaan ka accountant roz note karta hai ki kitna GST collect hua, kitna ITC milega, aur CA ko kya report bhejni hai — wahi kaam ye system automatically karta hai.
> Aur agar kabhi GST officer aaye toh compliance checklist se pata chalega ki kya kya ready hai.

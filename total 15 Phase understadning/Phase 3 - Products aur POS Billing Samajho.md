# Phase 3 — Products CRUD + POS Billing

## Layman mein samjho:

Phase 1 mein dukaan ka structure banaya tha (server + database).
Phase 2 mein taala lagaya tha (login system).
**Phase 3 mein dukaan mein samaan bhara aur billing machine lagayi.**

---

## Kya bana Phase 3 mein?

### Part A: Products (Samaan ka register)

| Kya | Matlab |
|---|---|
| **Product Add** | Naya product daal — naam, price, barcode, GST, stock |
| **Product List** | Saare products ki list dekho |
| **Product Search** | "Amul" likho — Amul ke saare products dikhao |
| **Product Update** | Price badhao, stock update karo |
| **Product Delete** | Product band karo (soft delete — data rehta hai, dikhta nahi) |
| **Stock Update** | Quick stock adjust — +20 aaya, -5 bika |

### Part B: POS Billing (Bill kaato)

| Kya | Matlab |
|---|---|
| **Create Bill** | Cart mein items daalo → bill banta hai → stock auto-minus |
| **Invoice Number** | INV-2026-0001 format mein automatic generate hota hai |
| **GST Auto Calculate** | Har item ka GST alag — system khud calculate karta hai |
| **Payment Modes** | Cash, UPI, Card, Udhaar — sab supported |
| **Udhaar** | Udhaar select kare toh payment_status = "pending" |
| **Today Summary** | Aaj kitne bill bane, kitna cash/upi/card/udhaar aaya |
| **Bill List** | Saare bills ki list with filter |
| **Bill Detail** | Ek bill ki full detail with items |

---

## 20 Demo Products Daale:

Amul Butter, Tata Salt, Maggi, Parle-G, Amul Milk, Fortune Oil, Aashirvaad Atta, Coca-Cola, Surf Excel, Haldiram Namkeen, Red Label Tea, Vim Bar, Dettol Soap, Britannia Bread, Kurkure, Colgate, Thums Up, Clinic Plus, Sugar, Lay's

---

## Test Results:

| Test | Result |
|---|---|
| Product list | 20 products dikhaye |
| Search "Amul" | 2 results (Butter + Milk) |
| Bill #1 (Amul Butter x2 + Maggi x5) | INV-2026-0001, Rs 656.40, UPI |
| Bill #2 (Tata Salt x3 + Coca-Cola x2) | INV-2026-0002, Rs 186.40, Udhaar (pending) |
| Stock auto-update | Amul Butter 50 → 48 |
| Stock manual +20 Maggi | 195 → 215 |
| Today Summary | 2 bills, Rs 842.80 total |

---

## Files banaye Phase 3 mein:

| File | Kya karta hai |
|---|---|
| `app/schemas/product.py` | Product ka data format (add/update/response) |
| `app/schemas/order.py` | Bill ka data format (cart items, response) |
| `app/api/products.py` | Product ke 6 APIs (add, list, search, update, delete, stock) |
| `app/api/pos.py` | POS ke 4 APIs (bill banao, list, detail, today summary) |
| `seed_products.py` | 20 demo FMCG products daalti hai |

---

## Dukaan ki bhasha mein:

> Phase 1 = Dukaan ka khali structure
> Phase 2 = Taala lagaya (login)
> **Phase 3 = Samaan bhara (20 products) + Billing machine lagayi (POS)**
>
> Ab dukaan mein product add ho sakte hain, bill kat sakte hain, stock track hota hai, aur din ki sale dekh sakte hain.

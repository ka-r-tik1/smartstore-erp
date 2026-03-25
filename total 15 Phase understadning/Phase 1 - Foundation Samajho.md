# Phase 1 — Foundation (Dukaan ka Khali Dhance)

---

## Ek Line Mein:
> **Phase 1 = Dukaan ka khali structure ready kiya. Deewarein hain, counter hai, register hai — but abhi koi samaan nahi, koi customer nahi, koi bill nahi.**

---

## Dukaan ki Bhasha Mein Samjho

| Kya bana | Dukaan ki bhasha | Technical naam |
|---|---|---|
| **Server** | Dukaan ka darwaza khola — ab koi aa sakta hai | FastAPI server at localhost:8000 |
| **Database** | Ek khaali register rakh diya counter pe | smartstore.db (SQLite file) |
| **5 Tables** | Register mein 5 sections banaye | Products, Dealers, Orders, Staff, Users tables |
| **Health API** | Ek bell lagayi — dabao toh "haan khuli hai" bole | /api/health |
| **Root API** | Dukaan ka naam board | / (root endpoint) |
| **Swagger UI** | Ek control panel — sab buttons browser mein dikhte hain | localhost:8000/docs |
| **Virtual Environment** | Dukaan ka apna godown | venv folder |

---

## 5 Tables (Registers) jo banaye — kya kya store hoga

| Table | Kya store karega |
|---|---|
| **Products** | Amul Butter, Tata Salt — naam, barcode, MRP, GST, stock |
| **Dealers** | Dealer ka naam, phone, udhaar baaki, GSTIN |
| **Orders** | Invoice number, total, GST, payment mode (cash/UPI) |
| **Staff** | Staff ka naam, role, salary |
| **Users** | Login ke liye username, password (bcrypt hashed) |

---

## Swagger UI — Control Panel kya hai?

**Swagger UI = Browser mein khulne wala remote control**

- URL: `http://localhost:8000/docs`
- Koi coding nahi chahiye — sirf button click karo
- Jo APIs banegi woh sab yahan button ke roop mein dikhti hain

### Swagger mein jo dikha:

```
GET  /api/health  → "Try it out" → Execute → Response aata hai
GET  /           → "Try it out" → Execute → Response aata hai
```

- **GET** = Sirf data maango (jaise "bhai chai ready hai?")
- **Try it out** = Button active karo
- **Execute** = API call karo
- **200** = Successful — kaam ho gaya
- **"string"** = Sirf example format — real execute karne pe actual data aata hai

### Real response jab execute karo:
```json
{
  "status": "healthy",
  "app": "SmartStore ERP",
  "message": "Backend chal raha hai!"
}
```

---

## Server Kaise Start Hota Hai?

```
cd "D:\claude only\NEW ERP START PROJECT\Backend files"
venv\Scripts\python main.py
```

Phir browser mein kholo: **http://localhost:8000/docs**

---

## Phase 1 mein kya NAHI tha?

- Koi products add nahi kiye (sirf table bani)
- Koi billing nahi (sirf orders ka dhanca bana)
- Koi login nahi (wo Phase 2 mein aaya)
- Koi real data nahi — sab khali registers

---

## Agle Phases mein kya hoga?

| Phase | Kya hoga |
|---|---|
| Phase 2 | Login system — username/password/JWT token |
| Phase 3 | Products add karo, POS billing shuru |
| Phase 4 | Inventory — stock management |
| Phase 5 | Dealers/Udhaar system |
| ... | aur baaki sab |

---

*Prepared by Claude | SmartStore ERP | Alphenta | March 2026*

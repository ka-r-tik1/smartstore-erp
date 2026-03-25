# Phase 2 — Login + JWT Auth (Dukaan ka Taala)

---

## Ek Line Mein:
> **Phase 2 = Dukaan mein taala lagaya. Ab sirf wahi andar aa sakta hai jiske paas chaabi hai — Owner, Cashier, ya Staff.**

---

## Dukaan ki Bhasha Mein Samjho

| Kya bana | Dukaan ki bhasha | Technical naam |
|---|---|---|
| **Register API** | Nayi chaabi banao — naya banda add karo | POST /api/auth/register |
| **Login API** | Chaabi daalo — andar aao, token lo | POST /api/auth/login |
| **Me API** | "Main kaun hun?" — token se pata chalta hai | GET /api/auth/me |
| **JWT Token** | Ek time-limited pass — 8 ghante valid | JSON Web Token |
| **Bcrypt** | Password ko ulta-seedha kar diya — koi padh nahi sakta | Password hashing |
| **3 Roles** | 3 tarah ki chaabiyaan — alag alag access | Owner / Cashier / Staff |

---

## 3 Roles — Kaun Kya Kar Sakta Hai

| Role | Kaun | Kya kar sakta hai |
|---|---|---|
| **Owner** | Tu — Kartik | Sab kuch — full access |
| **Cashier** | Counter pe baithne wala | Billing, POS, payments |
| **Staff** | Baaki employees | Limited access |

---

## JWT Token — Kya Hota Hai?

**Token = Ek temporary pass**

Jaise cinema hall mein ticket milti hai — andar jaate waqt dikhaao, time khatam toh invalid.

```
Login karo → Token milta hai → Har API call mein token bhejo → Server check karta hai → Access milta hai
```

- Token **8 ghante** valid hai (ek poori shift)
- Token expire ho gaya → dobara login karo
- Token galat hai → "Unauthorized" error aata hai

---

## Bcrypt — Password Safe Kaise Hota Hai?

**Plain password KABHI store nahi hota.**

```
Tu likhta hai:  "owner123"
Database mein:  "$2b$12$xK9mN3pQ..." (ulta-seedha code)
```

Jaise ek taala jo khulta toh hai sahi chaabi se, but chaabi dekhke taala nahi ban sakta.

- Koi bhi database dekhe — password nahi pata chalega
- Sirf bcrypt hi verify kar sakta hai sahi/galat

---

## 3 APIs jo Bane — Swagger Mein Kaise Dikhte Hain

### 1. Register — Naya User Banao
```
POST  /api/auth/register
```
Bhejo:
```json
{
  "username": "kartik",
  "password": "owner123",
  "full_name": "Kartik - Alphenta",
  "role": "owner"
}
```
Milega:
```json
{
  "id": 1,
  "username": "kartik",
  "role": "owner",
  "is_active": true
}
```
*Password response mein NAHI aata — secure hai*

---

### 2. Login — Token Lo
```
POST  /api/auth/login
```
Bhejo:
```json
{
  "username": "kartik",
  "password": "owner123"
}
```
Milega:
```json
{
  "access_token": "eyJhbGci...(lamba token)...",
  "token_type": "bearer",
  "user": { "id": 1, "username": "kartik", "role": "owner" }
}
```

---

### 3. Me — Kaun Logged In Hai?
```
GET  /api/auth/me
Header mein: Authorization: Bearer (token)
```
Milega:
```json
{
  "id": 1,
  "username": "kartik",
  "role": "owner",
  "is_active": true
}
```

---

## Swagger UI Mein Lock Icon

Phase 2 ke baad Swagger mein **🔒 lock icon** dikhega.

Matlab: Ye API protected hai — pehle login karo, token lo, phir use karo.

---

## Jo Test Kiya Humne

| Test | Result |
|---|---|
| Owner register (kartik) | ✅ Bana |
| Cashier register (raju_cashier) | ✅ Bana |
| Login → token mila | ✅ Kaam kiya |
| /me se user info aaya | ✅ Sahi data aaya |
| Duplicate username try kiya | ✅ Error aaya (blocked) |
| Galat role daala | ✅ Error aaya (blocked) |

---

## Bug Jo Fix Kiya

**bcrypt version mismatch** — naya bcrypt (5.0.0) purane passlib se compatible nahi tha.
Fix: bcrypt 4.0.1 install kiya. Kaam ho gaya.

---

## Phase 2 mein kya NAHI tha?

- Login screen (HTML wala) — wo abhi bhi nahi bana (Phase 13 mein banega)
- Products abhi bhi khaali hain
- Billing abhi bhi nahi hoti
- Ye sirf backend ka taala tha — frontend pe abhi koi button nahi

---

## Agle Phase mein kya hoga?

**Phase 3 = POS Billing**
- Products add karo database mein
- Product search API
- Cart banao
- Bill kato
- Order save karo

---

*Prepared by Claude | SmartStore ERP | Alphenta | March 2026*

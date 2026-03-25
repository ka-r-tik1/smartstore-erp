# Phase 14 — PWA + Offline Mode Samajho

## Ye Phase Kya Karta Hai?
SmartStore ko **phone pe app jaisi feel** deta hai aur **internet band hone pe bhi kaam karta hai.**

2 bade features:
1. **PWA (Progressive Web App)** — Android/iPhone pe install ho jata hai, app jaisa
2. **Offline Mode** — Internet nahi toh bhi billing hogi, baad mein sync hogi

---

## 1. PWA — Phone Pe Install Karo

### PWA Kya Hota Hai?
Normal website hoti hai browser mein kholta hoon.
PWA website hoti hai jo **phone ki home screen pe install** ho jaati hai — bilkul app ki tarah.

### Fayde:
| Feature | Normal Website | PWA |
|---|---|---|
| Home screen pe icon | ❌ | ✅ |
| Offline kaam karna | ❌ | ✅ |
| Fast loading | ❌ (har baar download) | ✅ (cache se) |
| Full screen | ❌ | ✅ |
| Push notifications | ❌ | ✅ (future) |

### Install Kaise Karein?
```
Chrome browser mein kholo → Address bar mein "Install" button aayega
→ Click karo → Home screen pe SmartStore icon aa jaayega
```

### Files Jo PWA Banati Hain:
| File | Kya hai |
|---|---|
| `manifest.json` | App ka naam, icon, theme color |
| `sw.js` | Service Worker — offline magic |

---

## 2. Service Worker — Offline Magic

### Service Worker Kya Hai?
Ek **background script** jo browser mein chalta rehta hai.
Interceptor ki tarah kaam karta hai — internet request ko rokta hai aur cache se deta hai.

### Flow:
```
User kuch maange → Service Worker check kare
     ↓
Online hai?  → Server se fresh data lo + cache mein save karo
Offline hai? → Cache se do (pehle se save tha)
```

### Cache Strategy:
```
Static Files (CSS/JS/HTML) → Cache First (fast loading)
API Calls (products/data)  → Network First (fresh data), cache fallback
POST requests (billing)    → Offline queue mein daalo
```

---

## 3. Offline POS — Internet Bina Billing

### Problem:
```
Dukaan mein internet chala gaya
→ Billing band ho jaaye? ❌ — Nahi hona chahiye!
```

### Solution:
```
Internet nahi → Bill banao → IndexedDB (browser storage) mein save
Internet wapas aaye → Automatic sync → Server pe bill process
```

### IndexedDB Kya Hai?
Browser ke andar ek **mini database** — jaise phone ka local storage.
Internet nahi toh bhi data yahan safe rehta hai.

### Offline Bill Flow:
```
Step 1: Cart bana lo (products cache se milenge)
Step 2: Bill Karo button dabaao
Step 3: "OFFLINE-1" number milega (temporary)
Step 4: Internet aane pe → Auto sync → Real invoice number milega
```

### Header mein dikhega:
```
● Online   (green — sab theek)
● Offline  (yellow — internet nahi)
↻ 3 Sync Pending  (yellow — 3 bills sync baaki hain)
```

---

## 4. Sync API — Offline Bills Server Pe Bhejo

### 2 APIs:
| # | API | Kya karta hai |
|---|---|---|
| 1 | POST /sync/offline-bill | Ek offline bill process karo |
| 2 | GET /sync/status | Server online check karo |

### Sync Process:
```
Internet aaya → SW background sync trigger
→ IndexedDB se pending bills nikalo
→ Ek ek karke /api/sync/offline-bill pe bhejo
→ Success → Bill "synced" mark karo
→ Header badge update (↻ 0 Sync Pending)
```

---

## 5. Frontend Structure

### Files:
```
Frontend/
├── index.html          → Main app (Login, Dashboard, POS, Stock, Alerts)
├── offline.html        → Internet nahi toh ye page
├── manifest.json       → PWA config
├── sw.js               → Service Worker
└── static/
    ├── css/
    │   └── style.css   → Dark theme, mobile-first design
    └── js/
        ├── app.js      → Login, Navigation, Dashboard, Inventory, Alerts
        ├── db.js       → IndexedDB wrapper (offline storage)
        ├── pos.js      → POS billing (online + offline)
        └── sync.js     → Offline bills sync logic
```

### 4 Pages (Single Page App):
| Page | Kya hai |
|---|---|
| Login | Username/Password |
| Dashboard | Aaj ki sale, alerts summary |
| POS | Billing (online + offline) |
| Stock | Inventory list, search |
| Alerts | Low stock, expiry, udhaar |

---

## 6. Backend Changes

### New File:
- `app/api/sync.py` — 2 sync APIs

### main.py Updates:
- `StaticFiles` mount — Frontend folder serve karo
- `/` → `index.html`
- `/sw.js` → Service Worker
- `/manifest.json` → PWA manifest
- `/offline.html` → Offline page

### Ab `http://localhost:8000/` kholo → Frontend dikhega!
(Pehle sirf `/docs` kaam karta tha)

---

## Test Kaise Karo

### 1. Server start karo:
```bash
cd "D:/claude only/NEW ERP START PROJECT/Backend files"
python main.py
```

### 2. Browser mein kholo:
```
http://localhost:8000/
```

### 3. Login karo:
```
Username: admin
Password: admin123
```

### 4. Offline test karo:
```
Chrome DevTools → Network tab → "Offline" select karo
→ POS mein bill banao → "OFFLINE-X" number aayega
→ "Online" wapas karo → Bills auto-sync honge
```

### 5. PWA Install karo:
```
Chrome mein address bar ke paas install icon → Click → Home screen pe aayega
```

---

## New Files Summary:

| File | Kya hai |
|---|---|
| `Frontend/index.html` | Main PWA app |
| `Frontend/offline.html` | Offline fallback page |
| `Frontend/manifest.json` | PWA config |
| `Frontend/sw.js` | Service Worker |
| `Frontend/static/css/style.css` | Dark theme UI |
| `Frontend/static/js/app.js` | Main app logic |
| `Frontend/static/js/db.js` | IndexedDB (offline storage) |
| `Frontend/static/js/pos.js` | Offline-capable POS |
| `Frontend/static/js/sync.js` | Auto-sync logic |
| `app/api/sync.py` | Backend sync API (2 APIs) |

## Total New APIs: 2

---

*Phase 14 Complete — 2026-03-21*

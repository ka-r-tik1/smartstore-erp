# Phase 11 — AI Modules Samajho (Forecast, Fraud, Chatbot)

## Ye Phase Kya Karta Hai?
Dukaan mein 3 AI features add kiye — bina kisi heavy ML library ke:
1. **Demand Forecast** — Product kitna bikega predict karo
2. **Fraud Detection** — Suspicious bills/transactions dhundho
3. **AI Chatbot** — Natural language (Hinglish) mein data poocho

---

## 1. DEMAND FORECAST — Kaise Kaam Karta Hai?

### Method: Moving Average + Growth Trend
```
Past 90 days ki daily sales data → Moving Average (7/30/overall) → Weighted Prediction
```

### Weighted Formula:
- 50% weight → Last 7 days average (recent trend)
- 30% weight → Last 30 days average (monthly pattern)
- 20% weight → Overall average (baseline)
- Growth factor: Last 30 vs Previous 30 days ka comparison

### APIs:
| API | Kya karta hai |
|-----|--------------|
| `GET /ai/forecast/product/{id}` | Ek product ki X-day demand forecast |
| `GET /ai/forecast/trending` | Top selling products (last X days) |
| `GET /ai/forecast/slow-moving` | Dead stock — jo bika hi nahi |
| `GET /ai/forecast/reorder-suggestions` | Kya mangwao, kitna, kab — AI suggest karega |

### Smart Features:
- Stock sufficient hai ya nahi → auto-check
- Reorder needed → suggested qty calculate karta hai (14 days worth)
- Dead stock value → kitna paisa fas raha hai

---

## 2. FRAUD DETECTION — Kaise Kaam Karta Hai?

### Method: Z-Score Anomaly Detection
```
Z-Score = (Value - Average) / Standard Deviation
Z > 2.0 = Suspicious | Z > 3.0 = Highly Suspicious
```

### Kya detect karta hai:
| Fraud Type | Kaise detect |
|-----------|-------------|
| Unusual bill amounts | Z-Score — bahut bada ya chota bill |
| High discounts | 20% se zyada discount = flag |
| Void/Return patterns | Return rate > 5% = investigate |
| Cash heavy | 70%+ cash = digital push karo |

### APIs:
| API | Kya karta hai |
|-----|--------------|
| `GET /ai/fraud/unusual-bills` | Abnormal amount ki bills |
| `GET /ai/fraud/unusual-discounts` | Zyada discount wali bills |
| `GET /ai/fraud/void-patterns` | Returns/voids pattern |
| `GET /ai/fraud/payment-anomaly` | Cash vs Digital breakup |
| `GET /ai/fraud/dashboard` | Ek jagah pe sab — risk score (0-100) |

### Risk Score (0-100):
- 0-29: LOW risk
- 30-59: MEDIUM risk
- 60-100: HIGH risk — investigate karo!

---

## 3. AI CHATBOT — Kaise Kaam Karta Hai?

### Method: Keyword Matching NLP
```
User message → Keyword scan → Intent detect → Database query → Response
```

### Supported Intents (10):
| Kya poocho | Example |
|-----------|---------|
| Aaj ki sale | "aaj kitni sale hui?" |
| Hafte ki sale | "week ki bikri batao" |
| Mahine ki sale | "month ki revenue" |
| Top products | "sabse zyada kya bika?" |
| Low stock | "stock mein kya kam hai?" |
| Stock value | "inventory kitna hai?" |
| Expiry alert | "kya expire hone wala hai?" |
| Udhaar summary | "udhaar kitna baaki?" |
| Product count | "kitne products hain?" |
| Profit estimate | "profit kitna hua?" |

### Special:
- **Hinglish supported** — "bikri", "maal", "baaki" sab samajhta hai
- **help** likhne pe saare commands bata deta hai

---

## Files Banaye:

### New Files (3):
| File | Kya hai |
|------|---------|
| `app/api/ai_forecast.py` | 4 Forecast APIs |
| `app/api/ai_fraud.py` | 5 Fraud Detection APIs |
| `app/api/ai_chatbot.py` | 1 Chatbot API (10 intents) |

### Modified Files (1):
| File | Kya change kiya |
|------|----------------|
| `main.py` | 3 AI routers register kiye |

---

## Total APIs: 10 endpoints

| # | Endpoint | Kya karta hai |
|---|----------|--------------|
| 1 | `/api/ai/forecast/product/{id}` | Demand forecast |
| 2 | `/api/ai/forecast/trending` | Top selling |
| 3 | `/api/ai/forecast/slow-moving` | Dead stock |
| 4 | `/api/ai/forecast/reorder-suggestions` | Kya mangwao |
| 5 | `/api/ai/fraud/unusual-bills` | Abnormal bills |
| 6 | `/api/ai/fraud/unusual-discounts` | High discounts |
| 7 | `/api/ai/fraud/void-patterns` | Return pattern |
| 8 | `/api/ai/fraud/payment-anomaly` | Cash vs Digital |
| 9 | `/api/ai/fraud/dashboard` | Risk score |
| 10 | `/api/ai/chatbot/ask` | Hinglish chatbot |

---

## Key Points:
1. **No ML library needed** — sab pure Python mein (math + statistics)
2. **Z-Score** = kitna abnormal hai koi value (school ka standard deviation concept)
3. **Moving Average** = last X days ka average → future predict
4. **Chatbot** = keyword matching, not real NLP — par kaam chal jayega
5. **Hinglish** = Hindi + English dono keywords support

---

*Phase 11 Complete — 2026-03-21*

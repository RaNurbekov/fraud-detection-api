# 🛡️ Anti-Fraud Detection API

> **Hybrid real-time fraud detection microservice**
> Redis Velocity Check + LightGBM + A/B Testing Router — production-ready architecture

---

## 🚀 Live Demo

| Endpoint | Link |
|---|---|
| 🏠 **API Root** | [fraud-detection-api-1-hf78.onrender.com](https://fraud-detection-api-1-hf78.onrender.com) |
| 📖 **Swagger UI** | [fraud-detection-api-1-hf78.onrender.com/docs](https://fraud-detection-api-1-hf78.onrender.com/docs) |
| ❤️ **Health Check** | [fraud-detection-api-1-hf78.onrender.com/health](https://fraud-detection-api-1-hf78.onrender.com/health) |
| 💳 **Test Cards** | [fraud-detection-api-1-hf78.onrender.com/cards](https://fraud-detection-api-1-hf78.onrender.com/cards) |

---

## 📊 Architecture — Hybrid Fraud Guardian

```
Incoming Transaction (card_id + amount only)
        │
        ▼
┌─────────────────────────────────────────┐
│   Layer 1: Redis Velocity Check         │
│   Checks transaction frequency          │
│   Protection against brute force        │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│   Redis Feature Store                   │
│   Client sends only card_id + amount    │
│   API fetches full historical profile   │
│   (V1-V28 features) from Redis          │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│   A/B Testing Router                    │
│   80% → Model A (Champion)              │
│   20% → Model B (Challenger)            │
│   Safe testing of new hypotheses        │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│   LightGBM Inference                    │
│   Class Imbalance handling              │
│   Fraud probability → APPROVE / BLOCK   │
└─────────────────────────────────────────┘
```

---

## 🛠 Tech Stack

| Component | Technology |
|---|---|
| **Machine Learning** | LightGBM (Class Imbalance handling) |
| **Feature Store** | Redis (Upstash — in-memory profiles) |
| **Backend** | FastAPI, Pydantic |
| **A/B Testing** | Custom 80/20 Champion/Challenger Router |
| **Containerization** | Docker, Docker Compose |
| **Deployment** | Render |
| **Dataset** | MLG-ULB Credit Card Fraud (Kaggle) |

---

## 🔑 Key Features

### 1. Redis Feature Store
Client sends only `card_id` and `amount` — the API fetches the full historical profile (V1-V28 features) from Redis automatically. This mirrors production anti-fraud systems at Visa and Mastercard:

```python
# Client sends minimal data
{"card_id": "card_0001", "amount": 500.00}

# API enriches with Redis profile internally
features = cache.get(f"profile:{card_id}")  # V1-V28 from Redis
features["Amount"] = amount                  # Add current transaction
```

### 2. A/B Testing Router (Champion/Challenger)
Built-in traffic splitter tests new model versions safely in production:

```python
if random.random() < 0.20:
    active_model = ml_models["model_b"]  # Challenger — 20%
else:
    active_model = ml_models["model_a"]  # Champion — 80%
```

No downtime, no risk — new models proven before full rollout.

### 3. Class Imbalance Handling
Credit card fraud datasets are heavily imbalanced (0.17% fraud). LightGBM trained with `scale_pos_weight` to properly detect rare fraud events.

---

## ⚡ API Reference

### GET /
```json
{
  "service": "Anti-Fraud Detection API",
  "architecture": "Hybrid: Redis Feature Store + LightGBM",
  "features": {
    "ab_testing": "80/20 Champion/Challenger split",
    "feature_store": "Redis in-memory profiles (Upstash)",
    "model": "LightGBM with Class Imbalance handling"
  }
}
```

### GET /health
```json
{
  "status": "healthy",
  "redis": "connected",
  "models_loaded": ["model_a", "model_b"],
  "ab_split": "80% Model A / 20% Model B"
}
```

### GET /cards
```json
{
  "available_cards": ["card_0001", "card_0002", "..."],
  "total": 101,
  "test_cards": {
    "normal": "card_0001",
    "fraud": "fraud_card_001"
  }
}
```

### POST /scan

**Normal transaction:**
```json
// Request
{
  "card_id": "card_0001",
  "amount": 500.00
}

// Response
{
  "card_id": "card_0001",
  "amount": 500.0,
  "decision": "APPROVE",
  "risk_level": "LOW",
  "risk_probability": 0.0821,
  "model_used": "Model A (Champion)",
  "feature_store": "Redis (Upstash)"
}
```

**Fraud transaction:**
```json
// Request
{
  "card_id": "fraud_card_001",
  "amount": 150000.00
}

// Response
{
  "card_id": "fraud_card_001",
  "amount": 150000.0,
  "decision": "BLOCK",
  "risk_level": "HIGH",
  "risk_probability": 0.8934,
  "model_used": "Model A (Champion)",
  "feature_store": "Redis (Upstash)"
}
```

---

## 🚀 Quick Start (Local)

### 1. Clone the repository
```bash
git clone https://github.com/RaNurbekov/fraud-detection-api.git
cd fraud-detection-api
```

### 2. Start with Docker Compose
```bash
docker-compose up --build
```
This starts both Redis and FastAPI containers automatically.

### 3. Test the API
```bash
# Normal transaction
curl -X POST "http://localhost:8000/scan" \
  -H "Content-Type: application/json" \
  -d '{"card_id": "card_0001", "amount": 500}'

# Fraud transaction
curl -X POST "http://localhost:8000/scan" \
  -H "Content-Type: application/json" \
  -d '{"card_id": "fraud_card_001", "amount": 150000}'
```

---

## 📁 Project Structure

```
fraud-detection-api/
├── api.py                  # FastAPI: /scan, /health, /cards
├── src/
│   └── database.py         # SQLite audit logging
├── models/
│   ├── lgbm_fraud.pkl      # Champion model (Model A)
│   └── lgbm_fraud_b.pkl    # Challenger model (Model B)
├── notebooks/              # Training & EDA
├── docker-compose.yml      # Redis + FastAPI orchestration
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 🔮 Roadmap

| Feature | Description |
|---|---|
| **Streamlit Dashboard** | Visual A/B testing stats + fraud monitoring |
| **MLflow Integration** | Model versioning and experiment tracking |
| **Evidently AI** | Data drift monitoring in production |
| **PostgreSQL** | Replace SQLite with production-grade DB |
| **Kafka Integration** | Connect with kafka-fraud-streaming pipeline |

---

## 🔗 Related Projects

Part of a Fintech ML ecosystem:

- [**fraud-gnn**](https://github.com/RaNurbekov/fraud-gnn) — Graph Neural Networks for collaborative fraud detection
- [**credit-risk-api**](https://github.com/RaNurbekov/credit-scoring-ml-api.) — Credit scoring with MLflow + SHAP + Evidently AI
- [**kafka-fraud-streaming**](https://github.com/RaNurbekov/kafka_anti_fraud) — Real-time Kafka streaming pipeline

> 💡 **Production vision:** Kafka streams transactions → this API scores them in real-time →
> GNN catches collaborative fraud rings → credit-risk-api assesses customer risk.
> That's the complete fintech ML stack.

---

## 📫 Author

**Rashid Nurbekov** — ML Engineer | Fintech & Generative AI | Almaty, Kazakhstan 🇰🇿

[![Telegram](https://img.shields.io/badge/Telegram-@RaNurbek-2CA5E0?style=flat&logo=telegram&logoColor=white)](https://t.me/RaNurbek)
[![Email](https://img.shields.io/badge/Email-nurbekovrashidjob@gmail.com-D14836?style=flat&logo=gmail&logoColor=white)](mailto:nurbekovrashidjob@gmail.com)
[![GitHub](https://img.shields.io/badge/GitHub-RaNurbekov-181717?style=flat&logo=github&logoColor=white)](https://github.com/RaNurbekov)

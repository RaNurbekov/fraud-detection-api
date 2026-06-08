from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
import redis
import json
import random
import os
import numpy as np

ml_models = {}
cache = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global cache

    print("Loading Champion (Model A) and Challenger (Model B)...")
    ml_models["model_a"] = joblib.load('models/lgbm_fraud.pkl')
    ml_models["model_b"] = joblib.load('models/lgbm_fraud_b.pkl')

    print("Connecting to Redis Feature Store (Upstash)...")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    cache = redis.from_url(redis_url, decode_responses=True)

    # Auto-seed Redis if empty
    existing_keys = cache.keys("profile:*")
    if len(existing_keys) < 10:
        print("Redis is empty — seeding with sample profiles...")
        seed_redis(cache, ml_models["model_a"])

    print("✅ A/B Router ready!")
    yield
    ml_models.clear()
    cache.close()


def seed_redis(cache, model):
    """Seed Redis with sample card profiles"""
    feature_names = model.feature_name_

    np.random.seed(42)
    sample_cards = [f"card_{i:04d}" for i in range(100)]

    for card_id in sample_cards:
        profile = {}
        for feat in feature_names:
            if feat not in ['Amount', 'Time']:
                profile[feat] = float(np.random.randn())
        cache.set(
            f"profile:{card_id}",
            json.dumps(profile),
            ex=86400
        )

    # Add test fraud card
    fraud_profile = {}
    for feat in feature_names:
        if feat not in ['Amount', 'Time']:
            fraud_profile[feat] = float(np.random.randn() * 3)
    cache.set(
        "profile:fraud_card_001",
        json.dumps(fraud_profile),
        ex=86400
    )
    print(f"✅ Seeded {len(sample_cards) + 1} card profiles!")


app = FastAPI(
    title="Anti-Fraud Detection API",
    description="Hybrid fraud detection: Redis Velocity Check + LightGBM + A/B Testing",
    version="1.0.0",
    lifespan=lifespan
)


class Transaction(BaseModel):
    card_id: str
    amount: float


@app.get("/")
def root():
    return {
        "service": "Anti-Fraud Detection API",
        "architecture": "Hybrid: Redis Feature Store + LightGBM",
        "features": {
            "ab_testing": "80/20 Champion/Challenger split",
            "feature_store": "Redis in-memory profiles (Upstash)",
            "model": "LightGBM with Class Imbalance handling"
        },
        "endpoints": ["/scan", "/health", "/cards", "/docs"]
    }


@app.get("/health")
def health():
    try:
        cache.ping()
        redis_status = "connected"
    except Exception:
        redis_status = "disconnected"

    return {
        "status": "healthy",
        "redis": redis_status,
        "models_loaded": list(ml_models.keys()),
        "ab_split": "80% Model A / 20% Model B"
    }


@app.get("/cards")
def list_cards():
    """List available test card IDs"""
    keys = cache.keys("profile:*")
    card_ids = [k.replace("profile:", "") for k in keys[:20]]
    return {
        "available_cards": card_ids,
        "total": len(cache.keys("profile:*")),
        "test_cards": {
            "normal": "card_0001",
            "fraud": "fraud_card_001"
        }
    }


@app.post("/scan")
def scan_transaction(tx: Transaction):

    # 1. GET PROFILE FROM REDIS FEATURE STORE
    profile_str = cache.get(f"profile:{tx.card_id}")
    if not profile_str:
        raise HTTPException(
            status_code=404,
            detail=f"Card profile not found: {tx.card_id}. Use GET /cards to see available cards."
        )

    features = json.loads(profile_str)
    features["Amount"] = tx.amount
    features["Time"] = 0.0

    df = pd.DataFrame([features])

    # 2. A/B TESTING ROUTER
    if random.random() < 0.20:
        active_model = ml_models["model_b"]
        model_name = "Model B (Challenger)"
    else:
        active_model = ml_models["model_a"]
        model_name = "Model A (Champion)"

    # 3. ALIGN FEATURES
    df = df[active_model.feature_name_]

    # 4. PREDICT
    prob = active_model.predict_proba(df)[:, 1][0]

    decision = "BLOCK" if prob > 0.50 else "APPROVE"
    risk_level = (
        "HIGH" if prob > 0.7 else
        "MEDIUM" if prob > 0.4 else
        "LOW"
    )

    return {
        "card_id": tx.card_id,
        "amount": tx.amount,
        "decision": decision,
        "risk_level": risk_level,
        "risk_probability": round(float(prob), 4),
        "model_used": model_name,
        "feature_store": "Redis (Upstash)"
    }
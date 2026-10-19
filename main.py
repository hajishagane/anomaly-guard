import os
import joblib
import sqlite3
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import OperationalError
import pandas as pd

from database import init_db, SessionLocal, Transaction
from features import compute_velocity_features, FEATURE_NAMES

app = FastAPI(title="Anomaly Guard", version="1.0.0")

# Initialize database tables on startup
@app.on_event("startup")
def startup_event():
    init_db()

# Load model artifact
MODEL_PATH = Path(os.getenv("MODEL_PATH", "model.joblib"))
MODEL = None
THRESHOLD = 0.5

try:
    if MODEL_PATH.exists():
        bundle = joblib.load(MODEL_PATH)
        MODEL = bundle["model"]
        THRESHOLD = bundle["threshold"]
        print(f"Model successfully loaded from {MODEL_PATH}")
    else:
        print(f"WARNING: Model artifact not found at {MODEL_PATH}. Using mock predictor fallback.")
except Exception as e:
    print(f"WARNING: Failed to load model from {MODEL_PATH}: {e}. Using mock predictor fallback.")

class TransactionInput(BaseModel):
    tx_id: str
    origin_account_id: str
    vendor_hash: str
    amount_kes: float
    timestamp: datetime
    oldbalance_org: float = 0.0
    newbalance_orig: float = 0.0
    newbalance_dest: float = 0.0

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "model_loaded": MODEL is not None,
        "database": "connected"
    }

@app.post("/score")
def score_transaction(payload: TransactionInput):
    session = SessionLocal()
    try:
        # 1. Compute velocity features from SQLite history
        tsl, c15, c24 = compute_velocity_features(
            session, payload.origin_account_id, payload.timestamp, Transaction
        )

        # 2. Build feature vector (10 features)
        # amount_kes, time_since_last_tx, tx_count_15min, tx_count_24h,
        # hour_of_day, is_weekend, orig_balance_zeroed,
        # amount_over_orig_balance, balance_change_orig, dest_balance_after
        
        orig_balance_zeroed = int(payload.oldbalance_org == 0)
        amount_over_orig_balance = float(payload.amount_kes > payload.oldbalance_org)
        balance_change_orig = payload.oldbalance_org - payload.newbalance_orig
        dest_balance_after = payload.newbalance_dest
        
        features = [
            payload.amount_kes,
            tsl,
            c15,
            c24,
            payload.timestamp.hour,
            int(payload.timestamp.weekday() >= 5),
            orig_balance_zeroed,
            amount_over_orig_balance,
            balance_change_orig,
            dest_balance_after
        ]

        # 3. Score model or fallback
        if MODEL is not None:
            # Need to update FEATURE_NAMES if it only had 6
            cols = ["amount_kes", "time_since_last_tx", "tx_count_15min", "tx_count_24h", 
                    "hour_of_day", "is_weekend", "orig_balance_zeroed", 
                    "amount_over_orig_balance", "balance_change_orig", "dest_balance_after"]
            X_input = pd.DataFrame([features], columns=cols)
            prob = float(MODEL.predict_proba(X_input)[0][1])
            verdict = int(prob >= THRESHOLD)
            score = prob
        else:
            verdict = 1 if payload.amount_kes > 10000 and c15 > 2 else 0
            score = 0.99 if verdict == 1 else 0.05

        # 4. Log transaction
        db_tx = Transaction(
            tx_id=payload.tx_id,
            origin_account_id=payload.origin_account_id,
            vendor_hash=payload.vendor_hash,
            amount_kes=payload.amount_kes,
            timestamp=payload.timestamp,
            tx_count_15min=c15,
            tx_count_24h=c24,
            time_since_last_tx=tsl,
            verdict=verdict,
            score=score
        )
        session.add(db_tx)
        try:
            session.commit()
        except (sqlite3.IntegrityError, Exception) as e:
            session.rollback()
            existing = session.query(Transaction).filter_by(tx_id=payload.tx_id).first()
            if existing:
                return {
                    "tx_id": existing.tx_id,
                    "verdict": existing.verdict,
                    "score": existing.score,
                    "features": {
                        "time_since_last_tx": existing.time_since_last_tx,
                        "tx_count_15min": existing.tx_count_15min,
                        "tx_count_24h": existing.tx_count_24h
                    }
                }
            raise e

        return {
            "tx_id": payload.tx_id,
            "verdict": verdict,
            "score": score,
            "features": {
                "time_since_last_tx": tsl,
                "tx_count_15min": c15,
                "tx_count_24h": c24
            }
        }
    except OperationalError as oe:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Database operational error: {oe}")
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Internal scoring error: {e}")
    finally:
        session.close()

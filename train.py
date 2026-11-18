import pandas as pd
import numpy as np
import joblib
from xgboost import XGBClassifier
from sklearn.ensemble import IsolationForest
from sklearn.metrics import f1_score, precision_score, recall_score, classification_report

from features import FEATURE_NAMES

# Alias kept for readability; training uses the canonical 10-feature list.
MODEL_FEATURE_NAMES = FEATURE_NAMES


def train_models():
    df = pd.read_csv("processed_train.csv")
    print(f"Dataset: {len(df)} samples ({df.isFraud.sum()} fraud, {(df.isFraud==0).sum()} legitimate)")

    # Temporal split inside the training data for validation
    df = df.sort_values("step").reset_index(drop=True)
    split_idx = int(len(df) * 0.8)
    train = df.iloc[:split_idx]
    val = df.iloc[split_idx:]

    X_train = train[MODEL_FEATURE_NAMES].values
    y_train = train["isFraud"].values
    X_val = val[MODEL_FEATURE_NAMES].values
    y_val = val["isFraud"].values

    print(f"Training: {len(train)} samples ({y_train.sum()} fraud)")
    print(f"Validation: {len(val)} samples ({y_val.sum()} fraud)")

    # --- Isolation Forest baseline (no SMOTE) ---
    print("\n--- Isolation Forest Baseline ---")
    iso = IsolationForest(contamination=max(0.001, y_train.mean()), random_state=42, n_estimators=100)
    iso.fit(X_train)
    iso_preds = iso.predict(X_val)
    iso_preds = (iso_preds == -1).astype(int)
    iso_f1 = f1_score(y_val, iso_preds, zero_division=0)
    print(f"Isolation Forest -> F1: {iso_f1:.4f}")

    # --- XGBoost with scale_pos_weight (no SMOTE) ---
    print("\n--- Training XGBoost with scale_pos_weight ---")
    n_pos = max(1, (y_train == 1).sum())
    n_neg = (y_train == 0).sum()
    scale_pos_weight = n_neg / n_pos
    print(f"scale_pos_weight: {scale_pos_weight:.2f}")

    xgb = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.1,
        scale_pos_weight=scale_pos_weight,
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1,
    )
    xgb.fit(X_train, y_train)

    y_proba = xgb.predict_proba(X_val)[:, 1]

    # Sweep thresholds and pick the best F1
    best_f1, best_thresh = 0.0, 0.5
    for thresh in np.arange(0.05, 0.95, 0.05):
        preds = (y_proba >= thresh).astype(int)
        f1 = f1_score(y_val, preds, zero_division=0)
        if f1 > best_f1:
            best_f1, best_thresh = f1, thresh

    preds = (y_proba >= best_thresh).astype(int)
    print(f"\nXGBoost (threshold={best_thresh:.2f}) -> F1: {best_f1:.4f}, "
          f"Precision: {precision_score(y_val, preds, zero_division=0):.4f}, "
          f"Recall: {recall_score(y_val, preds, zero_division=0):.4f}")
    print("\nClassification Report (XGBoost):")
    print(classification_report(y_val, preds, zero_division=0))

    # Save the model AND the threshold together
    joblib.dump({"model": xgb, "threshold": best_thresh}, "model.joblib")
    print(f"\nSaved model.joblib (threshold={best_thresh:.2f})")


if __name__ == "__main__":
    train_models()

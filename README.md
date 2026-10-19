---
title: Anomaly Guard
emoji: 🛡️
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
---

# Anomaly Guard

Fraud detection microservice for financial transactions.

## Model performance

| Model | F1 Score |
| :--- | :--- |
| **XGBoost + Balance Features** | **0.9991** |
| XGBoost (No Balance) | 0.4772 |
| Isolation Forest (Baseline) | 0.2453 |

*Note: The high performance of the balance-augmented model reflects PaySim's post-transaction information availability, which is not typical of real-world scenarios. The performance gap highlights the sensitivity of fraud detection to feature selection.*

## API

- `GET /health`: Returns service status.
- `POST /score`: Accepts JSON transaction payload, returns fraud verdict and probability.

## Reproducing

1. Download PaySim dataset.
2. Run `preprocess.py` to generate splits.
3. Run `train.py` to produce `model.joblib`.

## Known limitations

- Audit logs persist only in ephemeral storage in the free tier of Hugging Face Spaces.
- Load testing is deferred to Sprint 3.

## Data protection

- Sensitive account IDs are handled internally; SQLite persistence is local to the container.

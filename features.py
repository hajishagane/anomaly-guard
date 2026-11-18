from datetime import timedelta

FEATURE_NAMES = [
    "amount_kes",
    "time_since_last_tx",
    "tx_count_1h",
    "tx_count_24h",
    "hour_of_day",
    "is_weekend",
    "orig_balance_zeroed",
    "amount_over_old_balance",
    "balance_change_orig",
    "dest_balance_after",
]

# The 10 features the trained model expects, in order.
MODEL_FEATURE_NAMES = FEATURE_NAMES

def compute_velocity_features(session, origin_account_id, timestamp, TransactionModel):
    """
    Query the transaction log for the given account in the past 24 hours prior to timestamp.
    Returns: (time_since_last_tx_in_minutes, tx_count_15min, tx_count_24h)
    For cold starts (no prior transactions in 24h window), returns (0.0, 0, 0).
    """
    cutoff_24h = timestamp - timedelta(hours=24)
    cutoff_15min = timestamp - timedelta(minutes=15)

    recent_txs = (
        session.query(TransactionModel)
        .filter(
            TransactionModel.origin_account_id == origin_account_id,
            TransactionModel.timestamp >= cutoff_24h,
            TransactionModel.timestamp < timestamp,
        )
        .all()
    )

    if not recent_txs:
        return (0.0, 0, 0)

    last_tx_time = max(tx.timestamp for tx in recent_txs)
    time_since_last_tx = (timestamp - last_tx_time).total_seconds() / 60.0

    tx_count_15min = sum(1 for tx in recent_txs if tx.timestamp >= cutoff_15min)
    tx_count_24h = len(recent_txs)

    return (float(time_since_last_tx), tx_count_15min, tx_count_24h)

import os
import pandas as pd
import numpy as np


def compute_offline_velocity(df):
    """
    Sort by origin account and step, then compute velocity features offline.
    - time_since_last_tx: minutes since last transaction for same account
    - tx_count_24h: rolling count in past 24 hourly steps
    - tx_count_15min: approximation since PaySim steps are hourly
    """
    df = df.sort_values(["origin_account_id", "step"]).reset_index(drop=True)

    df["time_since_last_tx"] = df.groupby("origin_account_id")["step"].diff() * 60.0
    df["time_since_last_tx"] = df["time_since_last_tx"].fillna(0.0)

    df["tx_count_24h"] = (
        df.groupby("origin_account_id")["step"]
        .transform(lambda x: x.rolling(window=24, min_periods=1).count())
        .fillna(0)
        .astype(int)
    )

    df["tx_count_15min"] = (df["time_since_last_tx"] == 0.0).astype(int)

    return df


def preprocess_paysim(input_path="paysim.csv",
                      train_output="processed_train.csv",
                      sim_output="processed_sim.csv"):
    if not os.path.exists(input_path):
        print(f"ERROR: {input_path} not found. Please place paysim.csv in the project root.")
        return False

    print(f"Loading {input_path}...")
    usecols = ["step", "type", "amount", "nameOrig", "nameDest", "isFraud"]
    df = pd.read_csv(input_path, usecols=usecols)

    df = df[df["type"].isin(["TRANSFER", "CASH_OUT", "PAYMENT"])].copy()

    df = df.rename(columns={
        "amount": "amount_kes",
        "nameOrig": "origin_account_id",
        "nameDest": "vendor_hash",
    })

    train_raw = df[df["step"] <= 500]
    sim_raw = df[(df["step"] > 500) & (df["step"] <= 600)]

    def stratified_sample(frame, n, seed=42):
        if len(frame) <= n:
            return frame.sample(frac=1, random_state=seed).reset_index(drop=True)
        fraud = frame[frame["isFraud"] == 1]
        legit = frame[frame["isFraud"] == 0]
        n_fraud = max(1, int(n * len(fraud) / len(frame)))
        n_legit = n - n_fraud
        if len(fraud) < n_fraud:
            n_fraud = len(fraud)
            n_legit = n - n_fraud
        if len(legit) < n_legit:
            n_legit = len(legit)

        return pd.concat([
            fraud.sample(n=n_fraud, random_state=seed),
            legit.sample(n=n_legit, random_state=seed),
        ]).sample(frac=1, random_state=seed).reset_index(drop=True)

    print("Sampling training set (85,000 rows)...")
    train_sample = stratified_sample(train_raw, 85_000)

    print("Sampling simulation set (15,000 rows)...")
    sim_sample = stratified_sample(sim_raw, 15_000)

    print("Computing velocity features for training split...")
    train_sample = compute_offline_velocity(train_sample)

    print("Computing velocity features for simulation split...")
    sim_sample = compute_offline_velocity(sim_sample)

    train_sample.to_csv(train_output, index=False)
    sim_sample.to_csv(sim_output, index=False)

    print(f"Wrote {train_output} ({len(train_sample)} rows)")
    print(f"Wrote {sim_output} ({len(sim_sample)} rows)")

    return True


if __name__ == "__main__":
    preprocess_paysim()

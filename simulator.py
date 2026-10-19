import os
import time
import requests
import pandas as pd

BASE_URL = os.getenv("BASE_URL", "http://localhost:7860")
CSV_PATH = "processed_sim.csv"

def run_simulator():
    if not os.path.exists(CSV_PATH):
        print(f"Error: {CSV_PATH} not found.")
        return

    sim_df = pd.read_csv(CSV_PATH).sort_values("step").reset_index(drop=True)
    
    print(f"Starting simulation. Sending {len(sim_df)} transactions to {BASE_URL}...")
    
    for _, row in sim_df.iterrows():
        payload = {
            "tx_id": f"sim-{row['step']}-{row.name}",
            "origin_account_id": row["origin_account_id"],
            "vendor_hash": row["vendor_hash"],
            "amount_kes": float(row["amount_kes"]),
            "timestamp": "2026-01-01T00:00:00",
            "oldbalance_org": float(row.get("oldbalance_org", 0.0)),
            "newbalance_orig": float(row.get("newbalance_orig", 0.0)),
            "newbalance_dest": float(row.get("newbalance_dest", 0.0)),
        }
        
        try:
            response = requests.post(f"{BASE_URL}/score", json=payload)
            if response.status_code == 200:
                print(f"Scored {payload['tx_id']}: {response.json()['verdict']}")
            else:
                print(f"Failed {payload['tx_id']}: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error: {e}")
            
        time.sleep(0.05)

if __name__ == "__main__":
    run_simulator()

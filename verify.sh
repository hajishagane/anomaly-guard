#!/usr/bin/env bash
set -e

BASE_URL="${1:?Usage: ./verify.sh https://your-space.hf.space}"

echo "=== 1. Health check ==="
curl -sf "${BASE_URL}/health" | tee /dev/stderr
echo ""

echo "=== 2. Score a sample transaction ==="
curl -sf -X POST "${BASE_URL}/score" \
  -H "Content-Type: application/json" \
  -d '{
    "tx_id": "verify-001",
    "origin_account_id": "C1",
    "vendor_hash": "M1",
    "amount_kes": 500.0,
    "timestamp": "2026-01-01T12:00:00"
  }' | tee /dev/stderr
echo ""

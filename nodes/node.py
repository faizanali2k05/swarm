"""Federated node entrypoint.

Reads its own local CSV (no other nodes' data is visible), trains a small
model, and submits flat weights + dataset hash to the backend. In LOOP=true
mode the node retrains and resubmits every ROUND_INTERVAL seconds, which is
how it behaves inside a Docker deployment.

Environment variables:
    NODE_ID           — 1, 2, or 3 (selects which local CSV to load)
    API_URL           — backend base URL (default http://127.0.0.1:8000)
    DATA_DIR          — directory containing this node's local CSV + schema.json
    LOCAL_DATA_FILE   — override CSV filename (default node{NODE_ID}_data.csv)
    LOOP              — "true" to keep training/submitting on a schedule
    ROUND_INTERVAL    — seconds between rounds when LOOP=true (default 60)
    EPOCHS            — local training epochs per round (default 30)
    LEARNING_RATE     — SGD lr (default 0.05)
    HIDDEN            — hidden layer width (default 64)
    SEED              — torch seed (default: NODE_ID, for reproducibility)
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from common import (
    encode_features,
    hash_rows,
    load_csv,
    load_schema,
    submit_to_backend,
    train_local,
)


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


NODE_ID = _env_int("NODE_ID", 1)
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
DATA_DIR = Path(os.getenv("DATA_DIR", str(Path(__file__).resolve().parent.parent / "data")))
LOCAL_DATA_FILE = os.getenv("LOCAL_DATA_FILE", f"node{NODE_ID}_data.csv")
LOOP = os.getenv("LOOP", "false").lower() == "true"
ROUND_INTERVAL = _env_int("ROUND_INTERVAL", 60)
EPOCHS = _env_int("EPOCHS", 30)
LEARNING_RATE = _env_float("LEARNING_RATE", 0.05)
HIDDEN = _env_int("HIDDEN", 64)
SEED = _env_int("SEED", NODE_ID)

DATA_PATH = DATA_DIR / LOCAL_DATA_FILE
SCHEMA_PATH = DATA_DIR / "schema.json"


def round_once() -> None:
    if not DATA_PATH.exists():
        print(f"[node {NODE_ID}] missing local data file {DATA_PATH}", file=sys.stderr)
        return
    if not SCHEMA_PATH.exists():
        print(f"[node {NODE_ID}] missing schema {SCHEMA_PATH}", file=sys.stderr)
        return

    rows = load_csv(DATA_PATH)
    schema = load_schema(SCHEMA_PATH)
    X, y = encode_features(rows, schema)

    weights, acc = train_local(X, y, epochs=EPOCHS, lr=LEARNING_RATE, hidden=HIDDEN, seed=SEED)
    data_hash = hash_rows(rows)
    n = len(rows)
    print(f"[node {NODE_ID}] trained on {n} rows  acc={acc:.4f}  hash={data_hash[:12]}…  → {API_URL}")

    try:
        r = submit_to_backend(API_URL, NODE_ID, weights, data_hash, acc, n)
        body = r.text[:300] if hasattr(r, "text") else str(r)
        print(f"[node {NODE_ID}] backend {getattr(r, 'status_code', '?')}: {body}")
    except Exception as e:
        print(f"[node {NODE_ID}] submit failed: {e}", file=sys.stderr)


def main() -> None:
    if LOOP:
        time.sleep(int(os.getenv("STARTUP_DELAY", "5")))
        while True:
            try:
                round_once()
            except Exception as e:
                print(f"[node {NODE_ID}] round error: {e}", file=sys.stderr)
            time.sleep(ROUND_INTERVAL)
    else:
        round_once()


if __name__ == "__main__":
    main()

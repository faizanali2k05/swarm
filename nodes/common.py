"""Shared helpers for federated nodes.

Each node uses these utilities to:
  - load its own local dataset (the only data it ever sees),
  - encode features into the shared schema's fixed-dim space,
  - train a small local model,
  - submit flat weights + dataset hash + accuracy + sample count to the backend.

No data ever leaves the node — only the trained weights and a hash do.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Tuple

import numpy as np
import torch
import torch.nn as nn


class SimpleNet(nn.Module):
    def __init__(self, input_size: int, hidden: int = 64, out: int = 2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size, hidden),
            nn.ReLU(),
            nn.Linear(hidden, out),
        )

    def forward(self, x):
        return self.net(x)


def get_flat_weights(model: nn.Module):
    flat = []
    for p in model.state_dict().values():
        flat.extend(p.detach().cpu().numpy().ravel().tolist())
    return flat


def load_csv(path: Path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [
            {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in r.items()}
            for r in reader
        ]


def load_schema(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def encode_features(rows: list, schema: dict) -> Tuple[np.ndarray, np.ndarray]:
    """Encode rows → (X, y) using the shared schema for consistent dims & scaling."""
    n = len(rows)

    num_cols = schema["numeric"]
    means = np.array([schema["numeric_mean"][c] for c in num_cols], dtype=np.float64)
    stds = np.array([schema["numeric_std"][c] for c in num_cols], dtype=np.float64)
    stds = np.where(stds == 0, 1.0, stds)
    num_arr = np.array([[float(r[c]) for c in num_cols] for r in rows], dtype=np.float64)
    num_arr = (num_arr - means) / stds

    cat_parts = []
    for col, cats in schema["categorical"].items():
        cat_to_idx = {c: i for i, c in enumerate(cats)}
        oh = np.zeros((n, len(cats)), dtype=np.float32)
        for i, r in enumerate(rows):
            v = r.get(col)
            if v in cat_to_idx:
                oh[i, cat_to_idx[v]] = 1.0
        cat_parts.append(oh)

    X = np.concatenate([num_arr.astype(np.float32)] + cat_parts, axis=1).astype(np.float32)

    label_to_idx = {c: i for i, c in enumerate(schema["label_classes"])}
    y = np.array([label_to_idx[r[schema["label"]]] for r in rows], dtype=np.int64)
    return X, y


def hash_rows(rows: list) -> str:
    """SHA-256 over a deterministic serialization of the local dataset.

    Logged on-chain for tamper-evident provenance — does not reveal the data.
    """
    payload = json.dumps(rows, sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()


def train_local(X: np.ndarray, y: np.ndarray, epochs: int = 30, lr: float = 0.05, hidden: int = 64, seed: int | None = None):
    if seed is not None:
        torch.manual_seed(seed)

    Xt = torch.tensor(X, dtype=torch.float32)
    yt = torch.tensor(y, dtype=torch.long)

    model = SimpleNet(input_size=Xt.shape[1], hidden=hidden, out=2)
    opt = torch.optim.SGD(model.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()

    model.train()
    for _ in range(epochs):
        logits = model(Xt)
        loss = loss_fn(logits, yt)
        opt.zero_grad()
        loss.backward()
        opt.step()

    model.eval()
    with torch.no_grad():
        preds = model(Xt).argmax(dim=1)
        acc = (preds == yt).float().mean().item()

    return get_flat_weights(model), acc


def submit_to_backend(api_url: str, node_id: int, weights, data_hash: str, accuracy: float, num_samples: int, timeout: int = 60):
    import requests

    payload = {
        "node_id": node_id,
        "weights": weights,
        "data_hash": data_hash,
        "accuracy": accuracy,
        "num_samples": num_samples,
    }
    return requests.post(api_url.rstrip("/") + "/submit_weights", json=payload, timeout=timeout)

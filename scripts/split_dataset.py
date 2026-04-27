"""One-time offline split of the master hospital dataset into per-node files.

This is a SETUP step. It runs once on the demo author's machine BEFORE any
docker images are built. The server never invokes it. Each node image is
later built containing only the slice belonging to that node — the backend
never sees any raw patient data.

Distribution (designed to showcase FedAvg with unequal partitions):
    node1: 2/3 of the dataset
    node2: ~1/6 of the dataset
    node3: ~1/6 of the dataset

A `schema.json` is also produced from the full dataset (categorical levels,
numeric mean/std) so every node encodes features into the same fixed-
dimensional space and standardizes identically. Sharing schema metadata
across nodes is a standard simplification for federated demos; in a real
deployment you'd negotiate this offline once between participants.

Run from the repo root:
    python scripts/split_dataset.py
"""
import csv
import json
import random
from pathlib import Path

SEED = 42
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SOURCE = DATA_DIR / "hospital_data_analysis.csv"

NUMERIC_COLS = ["Age", "Cost", "Length_of_Stay", "Satisfaction"]
CATEGORICAL_COLS = ["Gender", "Condition", "Procedure"]
LABEL_COL = "Readmission"
DROP_COLS = ["Patient_ID", "Outcome"]


def main():
    with open(SOURCE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [
            {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in r.items()}
            for r in reader
        ]
    print(f"Loaded {len(rows)} rows from {SOURCE.name}")

    random.seed(SEED)
    random.shuffle(rows)

    n = len(rows)
    n1 = (n * 2) // 3
    rest = n - n1
    n2 = rest // 2
    n3 = rest - n2

    node1 = rows[:n1]
    node2 = rows[n1 : n1 + n2]
    node3 = rows[n1 + n2 :]

    print(f"  Node 1: {len(node1)} rows  ({len(node1)/n:.1%})")
    print(f"  Node 2: {len(node2)} rows  ({len(node2)/n:.1%})")
    print(f"  Node 3: {len(node3)} rows  ({len(node3)/n:.1%})")

    fieldnames = list(rows[0].keys())

    def write_csv(path, data):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(data)

    write_csv(DATA_DIR / "node1_data.csv", node1)
    write_csv(DATA_DIR / "node2_data.csv", node2)
    write_csv(DATA_DIR / "node3_data.csv", node3)

    schema = {
        "numeric": NUMERIC_COLS,
        "numeric_mean": {},
        "numeric_std": {},
        "categorical": {},
        "label": LABEL_COL,
        "label_classes": sorted({r[LABEL_COL] for r in rows}),
        "drop": DROP_COLS,
    }

    for col in NUMERIC_COLS:
        vals = [float(r[col]) for r in rows]
        mean = sum(vals) / len(vals)
        var = sum((v - mean) ** 2 for v in vals) / max(len(vals) - 1, 1)
        std = var**0.5 if var > 0 else 1.0
        schema["numeric_mean"][col] = mean
        schema["numeric_std"][col] = std

    for col in CATEGORICAL_COLS:
        schema["categorical"][col] = sorted({r[col] for r in rows})

    with open(DATA_DIR / "schema.json", "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)

    feature_dim = len(NUMERIC_COLS) + sum(len(v) for v in schema["categorical"].values())
    print(f"Schema written to {DATA_DIR / 'schema.json'}")
    print(f"Feature dim: {feature_dim}  |  Label classes: {schema['label_classes']}")


if __name__ == "__main__":
    main()

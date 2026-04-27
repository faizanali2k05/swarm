"""FastAPI backend for the SwarmChain federated demo.

The backend never sees raw patient data. Nodes train locally on their own
private slices and POST flattened weights + a SHA-256 dataset hash + the
sample count. The backend:

  1. Aggregates weights with sample-weighted FedAvg once one submission per
     expected node has arrived.
  2. Also computes the naive equal-weight aggregation in parallel — useful
     for visualizing why FedAvg's sample weighting matters when partitions
     are unequal (here: 2/3, 1/6, 1/6).
  3. Optionally writes the dataset hash on-chain for tamper-evident
     provenance (best-effort; degrades gracefully when no contract is
     configured).

State is in-memory — fine for a demo, not production.
"""
import os
import subprocess
import threading
from pathlib import Path
from typing import List, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from aggregator import average_flat_weights
import blockchain as bc

load_dotenv()

API_PORT = int(os.getenv("PORT", os.getenv("API_PORT", 8000)))
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
NUM_NODES_PER_ROUND = int(os.getenv("NUM_NODES_PER_ROUND", "3"))

app = FastAPI(title="SwarmChain Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Submission(BaseModel):
    node_id: int
    weights: List[float]
    data_hash: str
    accuracy: float = 0.0
    num_samples: int = 1


submissions: List[Submission] = []
rounds: int = 0
weighted_accuracies: List[float] = []
unweighted_accuracies: List[float] = []
last_round_summary: Dict | None = None
latest_weights: List[float] | None = None


def _aggregate_and_record():
    """Aggregate the current submissions, advance the round, return a summary."""
    global rounds, latest_weights, last_round_summary

    flat_list = [s.weights for s in submissions]
    sample_counts = [s.num_samples for s in submissions]
    total = float(sum(sample_counts)) or 1.0

    weighted_avg = average_flat_weights(flat_list, sample_counts)
    unweighted_avg = average_flat_weights(flat_list, None)

    weighted_acc = sum(s.accuracy * s.num_samples for s in submissions) / total
    unweighted_acc = sum(s.accuracy for s in submissions) / len(submissions)

    rounds += 1
    weighted_accuracies.append(weighted_acc)
    unweighted_accuracies.append(unweighted_acc)
    latest_weights = weighted_avg

    per_node = [
        {
            "node_id": s.node_id,
            "num_samples": s.num_samples,
            "share": s.num_samples / total,
            "accuracy": s.accuracy,
        }
        for s in submissions
    ]
    weight_l2_diff = (
        sum((a - b) ** 2 for a, b in zip(weighted_avg, unweighted_avg)) ** 0.5
        if weighted_avg and unweighted_avg
        else 0.0
    )

    last_round_summary = {
        "round": rounds,
        "weighted_accuracy": weighted_acc,
        "unweighted_accuracy": unweighted_acc,
        "weight_l2_diff": weight_l2_diff,
        "per_node": per_node,
    }
    submissions.clear()
    return last_round_summary


@app.post("/submit_weights")
def submit_weights(s: Submission):
    """Receive a weight submission from a node and aggregate when the round is full.

    De-duplicates by node_id: a fresh submission from the same node replaces
    its prior one in the current round (so a fast node can't fill the round
    by itself).
    """
    for i, existing in enumerate(submissions):
        if existing.node_id == s.node_id:
            submissions[i] = s
            break
    else:
        submissions.append(s)

    try:
        tx = bc.add_record(s.node_id, s.data_hash)
    except Exception as e:
        tx = {"error": str(e)}

    if len(submissions) >= NUM_NODES_PER_ROUND:
        summary = _aggregate_and_record()
        return {"status": "aggregated", "tx": tx, **summary}

    return {
        "status": "queued",
        "submissions_in_round": len(submissions),
        "expected": NUM_NODES_PER_ROUND,
        "tx": tx,
    }


@app.post("/aggregate")
def manual_aggregate():
    if not submissions:
        raise HTTPException(status_code=400, detail="no submissions")
    return {"status": "aggregated", **_aggregate_and_record()}


@app.post("/simulate")
def simulate_training():
    """Local-dev convenience: spawn the node script three times as subprocesses.

    Has no effect when running in a Dockerized federated deployment — the
    nodes/ folder won't be present in the backend container, and each node
    runs as its own container with its own private data.
    """
    nodes_folder = Path(__file__).resolve().parent.parent / "nodes"
    script = nodes_folder / "node.py"
    if not script.exists():
        return {
            "status": "noop",
            "detail": "nodes/ folder not present — running in dockerized federated mode; nodes train automatically.",
        }

    threads = []
    for nid in (1, 2, 3):
        env = os.environ.copy()
        env["NODE_ID"] = str(nid)
        env["API_URL"] = f"http://127.0.0.1:{API_PORT}"
        env.setdefault("LOOP", "false")
        env.setdefault("DATA_DIR", str(Path(__file__).resolve().parent.parent / "data"))

        def run(p, e):
            subprocess.run(["python", str(p)], cwd=str(nodes_folder), env=e)

        t = threading.Thread(target=run, args=(script, env), daemon=True)
        t.start()
        threads.append(t)

    return {"status": "started", "spawned": len(threads)}


@app.get("/chain/records")
def chain_records():
    return bc.get_records()


@app.get("/status")
def status():
    return {
        "rounds": rounds,
        "accuracies": weighted_accuracies,
        "fedavg_accuracies": weighted_accuracies,
        "naive_accuracies": unweighted_accuracies,
        "submissions_in_round": len(submissions),
        "expected_nodes_per_round": NUM_NODES_PER_ROUND,
        "last_round": last_round_summary,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=API_PORT, reload=False)

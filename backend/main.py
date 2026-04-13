"""FastAPI backend for SwarmChain AI demo.

Endpoints:
- POST /submit_weights : nodes submit weights + data hash
- POST /aggregate : manual aggregation (not required)
- POST /simulate : start node scripts to simulate training
- GET /chain/records : fetch blockchain records
- GET /status : get rounds and accuracies
"""
import os
import subprocess
import threading
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import List

from model import SimpleNet, get_flat_weights, set_flat_weights
from aggregator import average_flat_weights
import blockchain as bc

load_dotenv()

API_PORT = int(os.getenv("PORT", os.getenv("API_PORT", 8000)))
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "*").split(",")
    if origin.strip()
]

app = FastAPI()
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


# In-memory storage (demo only)
submissions = []
global_model = SimpleNet()
rounds = 0
accuracies = []


@app.post("/submit_weights")
def submit_weights(s: Submission):
    """Receive weights from a node and log the data hash to blockchain."""
    submissions.append(s)
    # attempt to log on-chain (best-effort)
    try:
        tx = bc.add_record(s.node_id, s.data_hash)
    except Exception as e:
        tx = {"error": str(e)}
    # If we have 3 submissions, aggregate
    if len(submissions) >= 3:
        flat_list = [sub.weights for sub in submissions]
        avg = average_flat_weights(flat_list)
        set_flat_weights(global_model, avg)
        global rounds
        global accuracies
        rounds += 1
        # average reported accuracy
        avg_acc = sum([sub.accuracy for sub in submissions]) / len(submissions)
        accuracies.append(avg_acc)
        submissions.clear()
        return {"status": "aggregated", "rounds": rounds, "avg_accuracy": avg_acc, "tx": tx}
    return {"status": "queued", "tx": tx}


@app.post("/aggregate")
def manual_aggregate():
    if not submissions:
        raise HTTPException(status_code=400, detail="no submissions")
    flat_list = [sub.weights for sub in submissions]
    avg = average_flat_weights(flat_list)
    set_flat_weights(global_model, avg)
    global rounds
    global accuracies
    rounds += 1
    avg_acc = sum([sub.accuracy for sub in submissions]) / len(submissions)
    accuracies.append(avg_acc)
    submissions.clear()
    return {"status": "aggregated", "rounds": rounds, "avg_accuracy": avg_acc}


@app.post("/simulate")
def simulate_training():
    """Start node scripts concurrently to simulate nodes training and submitting."""
    nodes_folder = os.path.join(os.path.dirname(__file__), '..', 'nodes')
    scripts = ['node1.py', 'node2.py', 'node3.py']

    procs = []
    for s in scripts:
        path = os.path.join(nodes_folder, s)
        # run in background thread to avoid blocking
        def run(path):
            subprocess.run(["python", path], cwd=nodes_folder)

        t = threading.Thread(target=run, args=(path,))
        t.start()
        procs.append(t)

    return {"status": "started"}


@app.get('/chain/records')
def chain_records():
    return bc.get_records()


@app.get('/status')
def status():
    return {"rounds": rounds, "accuracies": accuracies}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='0.0.0.0', port=API_PORT, reload=False)

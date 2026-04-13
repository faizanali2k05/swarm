"""Node 3: same as node1 but different random seed."""
import hashlib
import json
import requests
import os
import sys
import pathlib
import numpy as np
import torch
import torch.nn as nn
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from backend.model import SimpleNet, get_flat_weights

API_URL = os.getenv('API_URL', 'http://127.0.0.1:8000')


def hash_dataset(X, y):
    payload = json.dumps({'X': X.tolist(), 'y': y.tolist()}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def train_and_send(node_id=3):
    digits = load_digits()
    X = digits.data
    y = digits.target
    X, _, y, _ = train_test_split(X, y, train_size=0.2, random_state=node_id)
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    X = torch.tensor(X, dtype=torch.float32)
    y = torch.tensor(y, dtype=torch.long)

    model = SimpleNet(input_size=X.shape[1], hidden=32, out=10)
    loss_fn = nn.CrossEntropyLoss()
    opt = torch.optim.SGD(model.parameters(), lr=0.01)

    model.train()
    for epoch in range(3):
        logits = model(X)
        loss = loss_fn(logits, y)
        opt.zero_grad()
        loss.backward()
        opt.step()

    model.eval()
    with torch.no_grad():
        preds = model(X).argmax(dim=1)
        acc = (preds == y).float().mean().item()

    data_hash = hash_dataset(X.numpy(), y.numpy())
    weights = get_flat_weights(model)

    payload = {
        'node_id': node_id,
        'weights': weights,
        'data_hash': data_hash,
        'accuracy': acc
    }
    r = requests.post(API_URL + '/submit_weights', json=payload)
    print('Node', node_id, 'submitted, response:', r.text)


if __name__ == '__main__':
    train_and_send(3)

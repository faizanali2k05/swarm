# Federated node image — one image per node, each containing ONLY that
# node's private slice of the dataset. The backend never sees this data.
#
# Build from the repo root with NODE_ID as a build arg:
#     docker build -f nodes/Dockerfile --build-arg NODE_ID=1 -t swarmchain-node1 .
#     docker build -f nodes/Dockerfile --build-arg NODE_ID=2 -t swarmchain-node2 .
#     docker build -f nodes/Dockerfile --build-arg NODE_ID=3 -t swarmchain-node3 .
#
# Run on a different machine, pointing at the backend:
#     docker run --rm -e NODE_ID=1 -e API_URL=https://your-backend swarmchain-node1
#
# Run scripts/split_dataset.py once before building so data/node{N}_data.csv
# and data/schema.json exist.

FROM python:3.11-slim

ARG NODE_ID=1

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY nodes/requirements.txt ./
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

COPY nodes/common.py nodes/node.py /app/

# Bake in only this node's private slice + the shared schema metadata.
COPY data/schema.json /data/schema.json
COPY data/node${NODE_ID}_data.csv /data/local_data.csv

ENV NODE_ID=${NODE_ID} \
    DATA_DIR=/data \
    LOCAL_DATA_FILE=local_data.csv \
    API_URL=http://backend:8000 \
    LOOP=true \
    ROUND_INTERVAL=60 \
    EPOCHS=30 \
    STARTUP_DELAY=8

CMD ["python", "node.py"]

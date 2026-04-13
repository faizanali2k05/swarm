SwarmChain-AI
===============

See subfolders for backend, frontend, blockchain, and nodes. Run backend first, deploy contract, then run nodes and frontend.

See `backend/requirements.txt` and `frontend/package.json` for dependencies.

Environment files
-----------------

- `frontend/.env` uses `VITE_API_URL`
- `backend/.env` uses `API_PORT`, `CORS_ORIGINS`, `WEB3_PROVIDER`, `CONTRACT_ADDRESS`, `ACCOUNT_ADDRESS`, `PRIVATE_KEY`
- `blockchain/.env` uses `WEB3_PROVIDER`, `ACCOUNT_ADDRESS`, `PRIVATE_KEY`

Copy the example files first:

```powershell
Copy-Item frontend/.env.example frontend/.env
Copy-Item backend/.env.example backend/.env
Copy-Item blockchain/.env.example blockchain/.env
```

Local run
---------

1. Install backend dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

2. Install frontend dependencies:

```powershell
cd frontend
npm install
cd ..
```

3. For local blockchain testing, start Ganache on `http://127.0.0.1:8545`.

4. Put a funded test account from Ganache into `blockchain/.env`:

```env
WEB3_PROVIDER=http://127.0.0.1:8545
ACCOUNT_ADDRESS=0x...
PRIVATE_KEY=...
```

5. Deploy the contract:

```powershell
cd blockchain
python deploy.py
cd ..
```

6. Copy the deployed contract address into `backend/.env` and keep the same account and RPC:

```env
API_PORT=8000
WEB3_PROVIDER=http://127.0.0.1:8545
CONTRACT_ADDRESS=0x...
ACCOUNT_ADDRESS=0x...
PRIVATE_KEY=...
```

7. Start the backend:

```powershell
cd backend
python main.py
```

8. In another terminal, start the frontend:

```powershell
cd frontend
npm run dev
```

9. Open the frontend URL shown by Vite, then click `Trigger Simulation`.

Deployment
----------

- Cloudflare Pages: deploy `frontend`
- Render: deploy `backend`
- Blockchain: deploy contract to Sepolia using a free RPC, not Ganache

For cloud deployment, use a testnet RPC URL in `WEB3_PROVIDER` such as the HTTPS endpoint from your MetaMask Developer dashboard. Keep `PRIVATE_KEY` only in backend env vars on Render and never in frontend env vars.

Free deployment plan
--------------------

1. Deploy the contract to Sepolia:

```env
WEB3_PROVIDER=https://sepolia.infura.io/v3/YOUR_KEY
ACCOUNT_ADDRESS=0x...
PRIVATE_KEY=...
```

Run:

```powershell
cd blockchain
python deploy.py
```

2. Create a Render web service from this repo using `render.yaml`.

Set these Render environment variables:

```env
CORS_ORIGINS=https://your-cloudflare-pages-domain.pages.dev
WEB3_PROVIDER=https://sepolia.infura.io/v3/YOUR_KEY
CONTRACT_ADDRESS=0x...
ACCOUNT_ADDRESS=0x...
PRIVATE_KEY=...
```

3. Deploy the frontend on Cloudflare Pages.

Use:

- Root directory: `frontend`
- Build command: `npm run build`
- Build output directory: `dist`

Set this Cloudflare Pages environment variable:

```env
VITE_API_URL=https://your-render-service.onrender.com
```

4. After deployment, update `CORS_ORIGINS` on Render with your final Cloudflare Pages domain if it changed.

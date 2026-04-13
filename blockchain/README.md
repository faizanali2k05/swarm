This folder contains the `SwarmChain.sol` contract and a `deploy.py` helper.

Steps:
1. Start Ganache (default RPC http://127.0.0.1:8545)
2. Create `blockchain/.env` with `ACCOUNT_ADDRESS` and `PRIVATE_KEY` and `WEB3_PROVIDER` if needed
3. Run `python deploy.py` to compile & deploy.
4. Copy the deployed address into `backend/.env` as `CONTRACT_ADDRESS`.

"""Simple Web3.py helpers to interact with the deployed contract."""
import os
import json
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

WEB3_PROVIDER = os.getenv("WEB3_PROVIDER", "http://127.0.0.1:8545")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
ACCOUNT_ADDRESS = os.getenv("ACCOUNT_ADDRESS")

w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER))


def load_abi():
    here = os.path.dirname(__file__)
    abi_path = os.path.join(here, '..', 'blockchain', 'SwarmChain_abi.json')
    if not os.path.exists(abi_path):
        return None
    with open(abi_path, 'r') as f:
        return json.load(f)


def get_contract():
    abi = load_abi()
    if not abi or not CONTRACT_ADDRESS:
        return None
    return w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=abi)


def add_record(node_id: int, data_hash: str):
    """Call contract to add a record. Requires PRIVATE_KEY and ACCOUNT_ADDRESS in env."""
    contract = get_contract()
    if contract is None or not PRIVATE_KEY or not ACCOUNT_ADDRESS:
        return {"error": "contract or address not configured"}
    nonce = w3.eth.get_transaction_count(ACCOUNT_ADDRESS)
    txn = contract.functions.addRecord(node_id, data_hash).build_transaction({
        'from': ACCOUNT_ADDRESS,
        'nonce': nonce,
        'gas': 3000000,
        'gasPrice': w3.to_wei('1', 'gwei')
    })
    signed = w3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
    raw_tx = getattr(signed, "raw_transaction", signed.rawTransaction)
    tx_hash = w3.eth.send_raw_transaction(raw_tx)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return dict(txHash=tx_hash.hex(), receipt=receipt)


def get_records():
    contract = get_contract()
    if contract is None:
        return []
    try:
        recs = contract.functions.getRecords().call()
        # getRecords returns tuple of arrays: nodeIds, hashes, timestamps
        node_ids, hashes, timestamps = recs
        out = []
        for i in range(len(node_ids)):
            out.append({
                'nodeId': node_ids[i],
                'dataHash': hashes[i],
                'timestamp': timestamps[i]
            })
        return out
    except Exception:
        return []

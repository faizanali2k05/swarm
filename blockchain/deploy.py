"""Compile and deploy the SwarmChain contract to a local Ganache instance.
Produces an ABI JSON file that the backend can use.
"""
import os
from solcx import compile_standard, install_solc
import json
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

RPC = os.getenv('WEB3_PROVIDER', 'http://127.0.0.1:8545')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
ACCOUNT = os.getenv('ACCOUNT_ADDRESS')

with open('SwarmChain.sol', 'r') as f:
    source = f.read()

print('Installing solc...')
install_solc('0.8.13')

compiled = compile_standard({
    'language': 'Solidity',
    'sources': {'SwarmChain.sol': {'content': source}},
    'settings': {'outputSelection': {'*': {'*': ['abi', 'evm.bytecode']}}}
}, solc_version='0.8.13')

contract_id = list(compiled['contracts']['SwarmChain.sol'].keys())[0]
abi = compiled['contracts']['SwarmChain.sol'][contract_id]['abi']
bytecode = compiled['contracts']['SwarmChain.sol'][contract_id]['evm']['bytecode']['object']

with open('SwarmChain_abi.json', 'w') as f:
    json.dump(abi, f)

w3 = Web3(Web3.HTTPProvider(RPC))
acct = ACCOUNT

if not acct or not PRIVATE_KEY:
    print('Set ACCOUNT_ADDRESS and PRIVATE_KEY in .env to deploy')
    exit(1)

Swarm = w3.eth.contract(abi=abi, bytecode=bytecode)
nonce = w3.eth.get_transaction_count(acct)
tx = Swarm.constructor().buildTransaction({'from': acct, 'nonce': nonce, 'gas': 4000000, 'gasPrice': w3.toWei('1', 'gwei')})
signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
print('Deploying contract, tx:', tx_hash.hex())
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print('Deployed at', receipt.contractAddress)

print('\nSave CONTRACT_ADDRESS to backend .env or export as env var')

This demo shows how an AEA can be used to maintain an oracle and how another AEA can request the oracle value.

## Discussion

**Oracle agents** are agents that have permission to update or validate updates to state variables in a smart contract and whose goal is to accurately estimate or predict some real world quantity or quantities.

This demonstration shows how to set up a simple oracle agent who deploys an oracle contract and updates the contract with a token price fetched from a public API. It also shows how to create an oracle client agent that can request the value from the oracle contract. 

## Preparation instructions
 
### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

## Demo

### Create the oracle AEA

Fetch the AEA that will deploy and update the oracle contract.

``` bash
aea fetch fetchai/coin_price_oracle:0.7.0
cd coin_price_oracle
aea install
aea build
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

Create the AEA that will deploy the contract.

``` bash
aea create coin_price_oracle
cd coin_price_oracle
aea add connection fetchai/http_client:0.18.0
aea add connection fetchai/ledger:0.14.0
aea add connection fetchai/p2p_libp2p:0.17.0
aea add skill fetchai/coin_price:0.6.0
aea add skill fetchai/simple_oracle:0.6.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<0.2.0,>=0.1.0"},
  "aea-ledger-ethereum": {"version": "<0.2.0,>=0.1.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.17.0
aea install
```

Then update the agent configuration with the default routing and cert requests:
``` bash
aea config set --type dict agent.default_routing \
'{
"fetchai/contract_api:0.12.0": "fetchai/ledger:0.14.0",
"fetchai/http:0.13.0": "fetchai/http_client:0.18.0",
"fetchai/ledger_api:0.11.0": "fetchai/ledger:0.14.0"
}'
aea config set --type list vendor.fetchai.connections.p2p_libp2p.cert_requests \
'[{"identifier": "acn", "ledger_id": "ethereum", "not_after": "2022-01-01", "not_before": "2021-01-01", "public_key": "fetchai", "save_path": ".certs/conn_cert.txt"}]'
```

And change the default ledger:
``` bash
aea config set agent.default_ledger ethereum
```

</p>
</details>

Additionally, create the private key for the oracle AEA. Generate and add a key for Ethereum use:

``` bash
aea generate-key ethereum
aea add-key ethereum
```

Next, create a private key used to secure the AEA's communications:
``` bash
aea generate-key fetchai fetchai_connection_private_key.txt
aea add-key fetchai fetchai_connection_private_key.txt --connection
```

Finally, certify the key for use by the connections that request that:
``` bash
aea issue-certificates
```

### Create the oracle client AEA

From a new terminal (in the same top-level directory), fetch the AEA that will deploy the oracle client contract and call the function that requests the coin price from the oracle contract.

``` bash
aea fetch fetchai/coin_price_oracle_client:0.4.0
cd coin_price_oracle_client
aea install
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

Create the AEA that will deploy the contract.

``` bash
aea create coin_price_oracle_client
cd coin_price_oracle_client
aea add connection fetchai/http_client:0.18.0
aea add connection fetchai/ledger:0.14.0
aea add skill fetchai/simple_oracle_client:0.5.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<0.2.0,>=0.1.0"},
  "aea-ledger-ethereum": {"version": "<0.2.0,>=0.1.0"}
}'
aea config set agent.default_connection fetchai/ledger:0.14.0
aea install
```

Then update the agent configuration with the default routing:
``` bash
aea config set --type dict agent.default_routing \
'{
"fetchai/contract_api:0.12.0": "fetchai/ledger:0.14.0",
"fetchai/http:0.13.0": "fetchai/http_client:0.18.0",
"fetchai/ledger_api:0.11.0": "fetchai/ledger:0.14.0"
}'
```

Change the default ledger:
``` bash
aea config set agent.default_ledger ethereum
```

</p>
</details>

Create the private key for the oracle client AEA. Generate and add a key for Ethereum use:

``` bash
aea generate-key ethereum
aea add-key ethereum
```

The oracle AEAs require either a locally running test node or a connection to a remote testnet.

### Setting up with a local Ganache node

The easiest way to test the oracle agents is to set up a local Ethereum test node using Ganache. This can be done by running the following docker command from the directory you started from (in a new terminal). This command will also fund the accounts of the AEAs:

``` bash
docker run -p 8545:8545 trufflesuite/ganache-cli:latest --verbose --gasPrice=0 --gasLimit=0x1fffffffffffff --account="$(cat coin_price_oracle/ethereum_private_key.txt),1000000000000000000000" --account="$(cat coin_price_oracle_client/ethereum_private_key.txt),1000000000000000000000"
```

<details><summary>Run the enclosed Python script (with <code>web3</code> installed) from the top-level directory to deploy a mock Fetch ERC20 contract and give some test FET to the client agent.</summary>
<p>

``` python
import json
import os
from web3 import Web3

FILE_DIR = os.path.dirname(os.path.realpath(__file__))
CONTRACT_PATH = os.path.join(FILE_DIR, "coin_price_oracle_client/vendor/fetchai/contracts/fet_erc20/build/FetERC20Mock.json")
ORACLE_PRIVATE_KEY_PATH = os.path.join(FILE_DIR, "coin_price_oracle/ethereum_private_key.txt")
CLIENT_PRIVATE_KEY_PATH = os.path.join(FILE_DIR, "coin_price_oracle_client/ethereum_private_key.txt")

# Solidity source code
with open(CONTRACT_PATH) as file:
    compiled_sol = json.load(file)

# web3.py instance
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

# Import oracle account from private key and set to default account
with open(ORACLE_PRIVATE_KEY_PATH) as file:
    private_key = file.read()
oracle_account = w3.eth.account.privateKeyToAccount(private_key)
w3.eth.defaultAccount = oracle_account.address

# Import client account from private key
with open(CLIENT_PRIVATE_KEY_PATH) as file:
    private_key = file.read()
client_account = w3.eth.account.privateKeyToAccount(private_key)

# Deploy mock Fetch ERC20 contract
FetERC20Mock = w3.eth.contract(abi=compiled_sol['abi'], bytecode=compiled_sol['bytecode'])

# Submit the transaction that deploys the contract
tx_hash = FetERC20Mock.constructor(
    name="FetERC20Mock",
    symbol="MFET",
    initialSupply=int(1e23),
    decimals_=18).transact()

# Wait for the transaction to be mined, and get the transaction receipt
tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)

# Print out the contract address
print("FetERC20Mock contract deployed at:", tx_receipt.contractAddress)

# Get deployed contract
fet_erc20_mock = w3.eth.contract(address=tx_receipt.contractAddress, abi=compiled_sol['abi'])

# Transfer some test FET to oracle client account
tx_hash = fet_erc20_mock.functions.transfer(client_account.address, int(1e20)).transact()
tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
```

</p>
</details>

### Set the ERC20 contract address for the oracle AEA:
``` bash
aea config set vendor.fetchai.skills.simple_oracle.models.strategy.args.erc20_address ERC20_ADDRESS
```
where `ERC20_ADDRESS` is in the output of the script above.

### Run the oracle AEA

Run the oracle agent. This will deploy a contract to the testnet, grant oracle permissions to the AEA's wallet address, and periodically update the contract with the latest price of FET (or whichever coin was specified).
``` bash
aea run
```

After a few moments, you should see the following notices in the logs:
``` bash
info: [coin_price_oracle] Oracle contract successfully deployed!
...
info: [coin_price_oracle] Oracle role successfully granted!
...
info: [coin_price_oracle] Oracle value successfully updated!
```
The oracle contract will continue to be updated with the latest retrieved coin price at the default time interval (every 15 seconds).

### Set the ERC20 and oracle contract addresses for the oracle client AEA:
``` bash
aea config set vendor.fetchai.skills.simple_oracle_client.models.strategy.args.erc20_address ERC20_ADDRESS
aea config set vendor.fetchai.skills.simple_oracle_client.models.strategy.args.oracle_contract_address ORACLE_ADDRESS
```
where `ORACLE_ADDRESS` appears in the `contractAddress` field of the contract deployment transaction.

### Run the oracle client AEA

Run the oracle client agent. This will deploy an oracle client contract to the testnet, approve the contract to spend tokens on behalf of the AEA, and periodically call the contract function that requests the latest price of FET (or whichever coin was specified).
``` bash
aea run
```

After a few moments, you should see the following notices in the logs:
``` bash
info: [coin_price_oracle_client] Oracle client contract successfully deployed!
...
info: [coin_price_oracle_client] Oracle client transactions approved!
...
info: [coin_price_oracle_client] Oracle value successfully requested!
```
The AEA will continue to request the latest coin price at the default time interval (every 15 seconds).

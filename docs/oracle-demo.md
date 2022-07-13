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
aea fetch fetchai/coin_price_oracle:0.17.2
cd coin_price_oracle
aea install
```

<details><summary>Alternatively, create from scratch (and customize the data source)</summary>
<p>

Create the AEA that will deploy the contract.

``` bash
aea create coin_price_oracle
cd coin_price_oracle
aea add connection fetchai/http_client:0.24.2
aea add connection fetchai/ledger:0.21.1
aea add connection fetchai/prometheus:0.9.2
aea add skill fetchai/advanced_data_request:0.7.2
aea add skill fetchai/simple_oracle:0.16.1
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<2.0.0,>=1.0.0"},
  "aea-ledger-ethereum": {"version": "<2.0.0,>=1.0.0"}
}'
aea config set agent.default_connection fetchai/ledger:0.21.1
aea install
```

Set the URL for the data request skill:
``` bash
aea config set --type str vendor.fetchai.skills.advanced_data_request.models.advanced_data_request_model.args.url "https://api.coingecko.com/api/v3/simple/price?ids=fetch-ai&vs_currencies=usd"
```

Specify the name and JSON path of the data to fetch from the API:
``` bash
aea config set --type list vendor.fetchai.skills.advanced_data_request.models.advanced_data_request_model.args.outputs '[{"name": "price", "json_path": "fetch-ai.usd"}]'
```

Set the name of the oracle value in the simple oracle skill:
``` bash
aea config set vendor.fetchai.skills.simple_oracle.models.strategy.args.oracle_value_name price
```

Then update the agent configuration with the default routing:
``` bash
aea config set --type dict agent.default_routing \
'{
"fetchai/contract_api:1.1.2": "fetchai/ledger:0.21.1",
"fetchai/http:1.1.2": "fetchai/http_client:0.24.2",
"fetchai/ledger_api:1.1.2": "fetchai/ledger:0.21.1"
}'
```

Update the default ledger.
``` bash
aea config set agent.default_ledger fetchai
```

Set the following configuration for the oracle skill:
``` bash
aea config set vendor.fetchai.skills.simple_oracle.models.strategy.args.ledger_id fetchai
aea config set vendor.fetchai.skills.simple_oracle.models.strategy.args.update_function update_oracle_value
```

</p>
</details>

This demo runs on the `fetchai` ledger by default. Set the following variable for use in the configuration steps:
``` bash
LEDGER_ID=fetchai
```

<details><summary>Alternatively, configure the agent to use an ethereum ledger</summary>
<p>

``` bash
LEDGER_ID=ethereum
```

Update the default ledger.
``` bash
aea config set agent.default_ledger ethereum
```

Set the following configuration for the oracle skill:
``` bash
aea config set vendor.fetchai.skills.simple_oracle.models.strategy.args.ledger_id ethereum
aea config set vendor.fetchai.skills.simple_oracle.models.strategy.args.update_function updateOracleValue
```

</p>
</details>

Additionally, create the private key for the oracle AEA. Generate and add a key for use with the ledger:
``` bash
aea generate-key $LEDGER_ID --add-key
```

If running on a testnet (not including Ganache), generate some wealth for your AEA:
``` bash
aea generate-wealth $LEDGER_ID
```

### Create the oracle client AEA

From a new terminal (in the same top-level directory), fetch the AEA that will deploy the oracle client contract and call the function that requests the coin price from the oracle contract.

``` bash
aea fetch fetchai/coin_price_oracle_client:0.12.2
cd coin_price_oracle_client
aea install
```

<details><summary>Alternatively, create from scratch</summary>
<p>

Create the AEA that will deploy the contract.

``` bash
aea create coin_price_oracle_client
cd coin_price_oracle_client
aea add connection fetchai/http_client:0.24.2
aea add connection fetchai/ledger:0.21.1
aea add skill fetchai/simple_oracle_client:0.13.1
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<2.0.0,>=1.0.0"},
  "aea-ledger-ethereum": {"version": "<2.0.0,>=1.0.0"}
}'
aea config set agent.default_connection fetchai/ledger:0.21.1
aea install
```

Then update the agent configuration with the default routing:
``` bash
aea config set --type dict agent.default_routing \
'{
"fetchai/contract_api:1.1.2": "fetchai/ledger:0.21.1",
"fetchai/http:1.1.2": "fetchai/http_client:0.24.2",
"fetchai/ledger_api:1.1.2": "fetchai/ledger:0.21.1"
}'
```

Set the default ledger:
``` bash
aea config set agent.default_ledger fetchai
```
Set the following configuration for the oracle client skill:
``` bash
aea config set vendor.fetchai.skills.simple_oracle_client.models.strategy.args.ledger_id fetchai
aea config set vendor.fetchai.skills.simple_oracle_client.models.strategy.args.query_function query_oracle_value
```

</p>
</details>

Similar to above, set a temporary variable `LEDGER_ID=fetchai` or `LEDGER_ID=ethereum`.

<details><summary>Follow these steps to configure for an ethereum ledger</summary>
<p>

Set the default ledger:
``` bash
aea config set agent.default_ledger ethereum
```
Set the following configuration for the oracle client skill:
``` bash
aea config set vendor.fetchai.skills.simple_oracle_client.models.strategy.args.ledger_id ethereum
aea config set vendor.fetchai.skills.simple_oracle_client.models.strategy.args.query_function queryOracleValue
```

</p>
</details>

Create the private key for the oracle client AEA. Generate and add a key for use on the ledger:

``` bash
aea generate-key $LEDGER_ID --add-key
```

If running on a testnet (not including Ganache), generate some wealth for your AEA:
``` bash
aea generate-wealth $LEDGER_ID
```

### Configuring a ledger

The oracle AEAs require either a locally running ledger node or a connection to a remote ledger. By default, they are configured to use the latest `fetchai` testnet.

<details><summary>Follow these steps to configure local Ethereum test node</summary>
<p>

The easiest way to test the oracle agents on an Ethereum-based ledger to set up a local test node using Ganache. This can be done by running the following docker command from the directory you started from (in a new terminal). This command will also fund the accounts of the AEAs:

``` bash
docker run -p 8545:8545 trufflesuite/ganache-cli:latest --verbose --gasPrice=0 --gasLimit=0x1fffffffffffff --account="$(cat coin_price_oracle/ethereum_private_key.txt),1000000000000000000000" --account="$(cat coin_price_oracle_client/ethereum_private_key.txt),1000000000000000000000"
```

Run the following Python script (with <code>web3</code> installed) from the top-level directory to deploy a mock Fetch ERC20 contract and give some test FET to the client agent.

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

Set the ERC20 contract address for the oracle AEA
``` bash
aea config set vendor.fetchai.skills.simple_oracle.models.strategy.args.erc20_address $ERC20_ADDRESS
```
as well as for the oracle client AEA
``` bash
aea config set vendor.fetchai.skills.simple_oracle_client.models.strategy.args.erc20_address $ERC20_ADDRESS
```
where `ERC20_ADDRESS` is in the output of the script above.

</p>
</details>

### Run the oracle AEA

Run the oracle agent. This will deploy a contract to the testnet, grant oracle permissions to the AEA's wallet address, and periodically update the contract with the latest price of FET (or whichever coin was specified).
``` bash
aea run
```

After a few moments, you should see the following notices in the logs:
``` bash
info: [coin_price_oracle] Oracle contract successfully deployed at address: ...
...
info: [coin_price_oracle] Oracle role successfully granted!
...
info: [coin_price_oracle] Oracle value successfully updated!
```
The oracle contract will continue to be updated with the latest retrieved coin price at the default time interval (every 15 seconds).

### Set the ERC20 and oracle contract addresses for the oracle client AEA:
``` bash
aea config set vendor.fetchai.skills.simple_oracle_client.models.strategy.args.oracle_contract_address $ORACLE_ADDRESS
```
where `ORACLE_ADDRESS` should be set to the address shown in the oracle AEA logs:
``` bash
Oracle contract successfully deployed at address: ORACLE_ADDRESS
```

### Run the oracle client AEA

Run the oracle client agent. This will deploy an oracle client contract to the testnet, approve the contract to spend tokens on behalf of the AEA, and periodically call the contract function that requests the latest price of FET (or whichever coin was specified).
``` bash
aea run
```

After a few moments, you should see the following notices in the logs:
``` bash
info: [coin_price_oracle_client] Oracle client contract successfully deployed at address: ...
...
info: [coin_price_oracle_client] Oracle value successfully requested!
```
The AEA will continue to request the latest coin price at the default time interval (every 15 seconds).

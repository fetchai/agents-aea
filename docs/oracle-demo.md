This demo shows how an AEA can be used to maintain an oracle.

## Discussion

**Oracle agents** are agents that have permission to update or validate updates to state variables in a smart contract and whose goal is to accurately estimate or predict some real world quantity or quantities.

This demonstration shows how to set up a simple oracle agent who deploys an oracle contract and updates the contract with a token price fetched from a public API.

## Preparation instructions
 
### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

## Demo

### Create the simple oracle AEA

Fetch the AEA that will deploy and update the oracle contract.

``` bash
aea fetch fetchai/coin_price_oracle:0.2.0
cd coin_price_oracle
aea install
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

Create the AEA that will deploy the contract.

``` bash
aea create coin_price_oracle
cd coin_price_oracle
aea add connection fetchai/http_client:0.15.0
aea add connection fetchai/ledger:0.11.0
aea add connection fetchai/p2p_libp2p:0.13.0
aea add skill fetchai/coin_price:0.2.0
aea add skill fetchai/simple_oracle:0.2.0
aea install
aea config set agent.default_connection fetchai/p2p_libp2p:0.13.0
```

Then update the agent config with the default routing:
``` bash
aea config set --type dict agent.default_routing \
'{
"fetchai/contract_api:0.9.0": "fetchai/ledger:0.11.0",
"fetchai/http:0.10.0": "fetchai/http_client:0.15.0",
"fetchai/ledger_api:0.8.0": "fetchai/ledger:0.11.0"
}'
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
aea add-key ethereum ethereum_private_key.txt
```


The oracle AEAs require either a locally runnning test node or a connection to a remote testnet.

### Setting up with a local Ganache node

The easiest way to test the oracle agents is to set up a local Ethereum test node using Ganache. This can be done by running the following docker command from the directory you started from (in a separate terminal). This command will also fund the account of the AEA:
``` bash
docker run -p 8545:8545 trufflesuite/ganache-cli:latest --verbose --gasPrice=0 --gasLimit=0x1fffffffffffff --account="$(cat coin_price_oracle/ethereum_private_key.txt),1000000000000000000000"
```

### Run the Oracle AEA

Run the oracle agent. This will deploy a contract to the testnet, grant oracle permissions to the AEA's wallet address, and periodically update the contract with the latest price of FET (or whichever coin was specified).
```bash
aea run
```

After a few moments, you should see the following notices in the logs:
```bash
info: [coin_price_oracle] Oracle contract successfully deployed!
...
info: [coin_price_oracle] Oracle role successfully granted!
...
info: [coin_price_oracle] Oracle value successfully updated!
```
The oracle contract will continue to be updated with the latest retrieved coin price at the default time interval (every 15 seconds).

*This demo will soon be extended to include an oracle client AEA who requests and purchases the oracle value with FET tokens.*

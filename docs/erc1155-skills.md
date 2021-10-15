The AEA `erc1155_deploy` and `erc1155_client` skills demonstrate an interaction between two AEAs which use a smart contract.

* The `erc1155_deploy` skill deploys the smart contract, creates and mints items. 
* The `erc1155_client` skill signs a transaction to complete a trustless trade with its counterparty.

## Preparation instructions
 
### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

## Discussion

The scope of this guide is demonstrating how you can deploy a smart contract and interact with it using AEAs. In this specific demo, you create two AEAs. One deploys and creates tokens inside a smart contract. The other signs a transaction to complete an atomic swap. The smart contract used is ERC1155 with a one-step atomic swap functionality. This means the trade between the two AEAs can be trustless.

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>This is only for demonstrative purposes since the AEA deploying the contract also has the ability to mint tokens. In reality, the transfer of tokens from the AEA signing the transaction is worthless.</p>
</div>

## Demo

### Create the deployer AEA

Fetch the AEA that will deploy the contract:

``` bash
aea fetch fetchai/erc1155_deployer:0.33.0
cd erc1155_deployer
aea install
aea build
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

Create the AEA that will deploy the contract.

``` bash
aea create erc1155_deployer
cd erc1155_deployer
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/ledger:0.19.0
aea add skill fetchai/erc1155_deploy:0.30.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<2.0.0,>=1.0.0"},
  "aea-ledger-ethereum": {"version": "<2.0.0,>=1.0.0"},
  "aea-ledger-cosmos": {"version": "<2.0.0,>=1.0.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.25.0
aea config set --type dict agent.default_routing \
'{
  "fetchai/contract_api:1.0.0": "fetchai/ledger:0.19.0",
  "fetchai/ledger_api:1.0.0": "fetchai/ledger:0.19.0",
  "fetchai/oef_search:1.0.0": "fetchai/soef:0.26.0"
}'
aea config set --type list vendor.fetchai.connections.p2p_libp2p.cert_requests \
'[{"identifier": "acn", "ledger_id": "ethereum", "not_after": "2022-01-01", "not_before": "2021-01-01", "public_key": "fetchai", "save_path": ".certs/conn_cert.txt"}]'
aea install
aea build
```

And change the default ledger:
``` bash
aea config set agent.default_ledger ethereum
```

</p>
</details>

Create a private key for the deployer AEA and add it for Ethereum use:

``` bash
aea generate-key ethereum
aea add-key ethereum ethereum_private_key.txt
```

Create a private key for the P2P connection:

``` bash
aea generate-key fetchai fetchai_connection_private_key.txt
aea add-key fetchai fetchai_connection_private_key.txt --connection
```

Finally, certify the key for use by the connections that request that:

``` bash
aea issue-certificates
```

### Create the client AEA

In another terminal, fetch the client AEA which will receive some tokens from the deployer.

``` bash
aea fetch fetchai/erc1155_client:0.33.0
cd erc1155_client
aea install
aea build
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

Create the AEA that will get some tokens from the deployer.

``` bash
aea create erc1155_client
cd erc1155_client
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/ledger:0.19.0
aea add skill fetchai/erc1155_client:0.28.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<2.0.0,>=1.0.0"},
  "aea-ledger-ethereum": {"version": "<2.0.0,>=1.0.0"},
  "aea-ledger-cosmos": {"version": "<2.0.0,>=1.0.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.25.0
aea config set --type dict agent.default_routing \
'{
  "fetchai/contract_api:1.0.0": "fetchai/ledger:0.19.0",
  "fetchai/ledger_api:1.0.0": "fetchai/ledger:0.19.0",
  "fetchai/oef_search:1.0.0": "fetchai/soef:0.26.0"
}'
aea config set --type list vendor.fetchai.connections.p2p_libp2p.cert_requests \
'[{"identifier": "acn", "ledger_id": "ethereum", "not_after": "2022-01-01", "not_before": "2021-01-01", "public_key": "fetchai", "save_path": ".certs/conn_cert.txt"}]'
aea install
aea build
```

And change the default ledger:
``` bash
aea config set agent.default_ledger ethereum
```

</p>
</details>

Create a private key for the client AEA and add it for Ethereum use:

``` bash
aea generate-key ethereum
aea add-key ethereum ethereum_private_key.txt
```

Create a private key for the P2P connection:

``` bash
aea generate-key fetchai fetchai_connection_private_key.txt
aea add-key fetchai fetchai_connection_private_key.txt --connection
```

Finally, certify the key for use by the connections that request that:
``` bash
aea issue-certificates
```

## Run Ganache

Execute the following command to run Ganache:
``` bash
docker run -p 8545:8545 trufflesuite/ganache-cli:latest --verbose --gasPrice=0 --gasLimit=0x1fffffffffffff --account="$(cat erc1155_deployer/ethereum_private_key.txt),1000000000000000000000" --account="$(cat erc1155_client/ethereum_private_key.txt),1000000000000000000000"
```

Wait some time for the wealth creation to be mined on Ropsten.

Check your wealth:

``` bash
aea get-wealth ethereum
```

You should get `1000000000000000000000`.

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>If no wealth appears after a while, then try funding the private key directly using a web faucet.</p>
</div>


## Update SOEF configurations for both AEAs

Update the SOEF configuration in both AEA projects:
``` bash
aea config set vendor.fetchai.connections.soef.config.chain_identifier ethereum
```

## Run the AEAs

First, run the deployer AEA:

``` bash 
aea run
```

Once you see a message of the form `To join its network use multiaddr 'SOME_ADDRESS'` take note of this address. 

Alternatively, use `aea get-multiaddress fetchai -c -i fetchai/p2p_libp2p:0.25.0 -u public_uri` to retrieve the address. The output will be something like `/dns4/127.0.0.1/tcp/9000/p2p/16Uiu2HAm2JPsUX1Su59YVDXJQizYkNSe8JCusqRpLeeTbvY76fE5`.

This is the entry peer address for the local <a href="../acn">agent communication network</a> created by the deployer.

This AEA then performs the following steps:

 * deploys the smart contract
 * creates a batch of items in the smart contract
 * mints a batch of items in the smart contract

At some point you should see the log output:
``` bash
registering service on SOEF.
```

At this point, configure the client AEA to connect to the same local ACN created by the deployer by running the following command in the client's terminal, replacing `SOME_ADDRESS` with the value you noted above:
``` bash
aea config set --type dict vendor.fetchai.connections.p2p_libp2p.config \
'{
  "delegate_uri": "127.0.0.1:11001",
  "entry_peers": ["SOME_ADDRESS"],
  "local_uri": "127.0.0.1:9001",
  "log_file": "libp2p_node.log",
  "public_uri": "127.0.0.1:9001"
}'
```

Then, run the client AEA:

``` bash 
aea run
```

You will see that after discovery, the two AEAs exchange information about the transaction and the client at the end signs and sends the signature to the deployer AEA to send it to the network.

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>Transactions on Ropsten can take a significant amount of time! If you run the example a second time, and the previous transaction is still pending, it can lead to a failure.

  The warning message `Cannot verify whether transaction improves utility. Assuming it does!` can be ignored.
  </p>
</div>

## Delete the AEAs

When you're done, stop the agents (`CTRL+C`), go up a level and delete the AEAs.

``` bash 
cd ..
aea delete erc1155_deployer
aea delete erc1155_client
```

## Communication

This diagram shows the communication between the various entities in this interaction:

<div class="mermaid">
    sequenceDiagram
        participant Search
        participant Erc1155_contract
        participant Client_AEA
        participant Deployer_AEA
        participant Blockchain

        activate Search
        activate Erc1155_contract
        activate Client_AEA
        activate Deployer_AEA
        activate Blockchain
        
        Deployer_AEA->>Blockchain: deployes smart contract
        Deployer_AEA->>ERC1155_contract: creates tokens
        Deployer_AEA->>ERC1155_contract: mint tokens       
        Deployer_AEA->>Search: register_service
        Client_AEA->>Search: search
        Search-->>Client_AEA: list_of_agents
        Client_AEA->>Deployer_AEA: call_for_proposal
        Deployer_AEA->>Client_AEA: inform_message
        Client_AEA->>Deployer_AEA: signature
        Deployer_AEA->>Blockchain: send_transaction
        Client_AEA->>ERC1155_contract: asks_balance
        
        deactivate Search
        deactivate Erc1155_contract
        deactivate Client_AEA
        deactivate Deployer_AEA
        deactivate Blockchain
       
</div>
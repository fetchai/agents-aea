The AEA `erc1155_deploy` and `erc1155_client` skills demonstrate an interaction between two AEAs with the usage of a smart contract.

* The `erc1155_deploy` skill deploys the smart contract, creates and mints items. 
* The `erc1155_client` skill signs a transaction to complete a trustless trade with the counterparty.

## Preparation instructions
 
### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

##Discussion

The scope of the specific demo is to demonstrate how to deploy a smart contract and interact with it. For the specific use-case, we create two AEAs one that deploys and creates tokens inside the smart contract and the other that signs a transaction so we can complete an atomic swap. The smart contract we are using is an ERC1155 smart contract
with a one-step atomic swap functionality. That means the trade between the two AEAs can be trustless.

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>This demo serves demonstrative purposes only. Since the AEA deploying the contract also has the ability to mint tokens, in reality the transfer of tokens from the AEA signing the transaction is worthless.</p>
</div>

### Launch an OEF node
In a separate terminal, launch a local OEF node (for search and discovery).
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

Keep it running for all the following demos.

## Demo

### Create the deployer AEA

Fetch the AEA that will deploy the contract.

``` bash
aea fetch fetchai/erc1155_deployer:0.7.0
cd erc1155_deployer
aea install
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

Create the AEA that will deploy the contract.

``` bash
aea create erc1155_deployer
cd erc1155_deployer
aea add connection fetchai/oef:0.5.0
aea add connection fetchai/ledger:0.1.0
aea add skill fetchai/erc1155_deploy:0.7.0
aea install
aea config set agent.default_connection fetchai/oef:0.5.0
```

Then update the agent config (`aea-config.yaml`) with the default routing:
``` yaml
default_routing:
  fetchai/contract_api:0.1.0: fetchai/ledger:0.1.0
  fetchai/ledger_api:0.1.0: fetchai/ledger:0.1.0
```

And change the default ledger:
``` bash
aea config set agent.default_ledger ethereum
```

</p>
</details>

Additionally, create the private key for the deployer AEA. Generate and add a key for Ethereum use:

``` bash
aea generate-key ethereum
aea add-key ethereum eth_private_key.txt
```

### Create the client AEA

In another terminal, fetch the AEA that will get some tokens from the deployer.

``` bash
aea fetch fetchai/erc1155_client:0.7.0
cd erc1155_client
aea install
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

Create the AEA that will get some tokens from the deployer.

``` bash
aea create erc1155_client
cd erc1155_client
aea add connection fetchai/oef:0.5.0
aea add connection fetchai/ledger:0.1.0
aea add skill fetchai/erc1155_client:0.6.0
aea install
aea config set agent.default_connection fetchai/oef:0.5.0
```

Then update the agent config (`aea-config.yaml`) with the default routing:
``` yaml
default_routing:
  fetchai/contract_api:0.1.0: fetchai/ledger:0.1.0
  fetchai/ledger_api:0.1.0: fetchai/ledger:0.1.0
```

And change the default ledger:
``` bash
aea config set agent.default_ledger ethereum
```

</p>
</details>

Additionally, create the private key for the client AEA. Generate and add a key for Ethereum use:

``` bash
aea generate-key ethereum
aea add-key ethereum eth_private_key.txt
```

### Update the AEA configs

Both in `erc1155_deployer/aea-config.yaml` and
`erc1155_client/aea-config.yaml`, replace `ledger_apis: {}` with the following based on the network you want to connect

Connect to Ethereum:
``` yaml
ledger_apis:
  ethereum:
    address: https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe
    chain_id: 3
    gas_price: 50
```

### Fund the AEAs

To create some wealth for your AEAs for the Ethereum `ropsten` network. Note that this needs to be executed from each AEA folder:

``` bash
aea generate-wealth ethereum
```

To check the wealth use (after some time for the wealth creation to be mined on Ropsten):

``` bash
aea get-wealth ethereum
```

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>If no wealth appears after a while, then try funding the private key directly using a web faucet.</p>
</div>

## Run the AEAs

First, run the deployer AEA.

``` bash 
aea run
```

It will perform the following steps:
- deploy the smart contract
- create a batch of items in the smart contract
- mint a batch of itemsin the smart contract

At some point you should see the log output:
``` bash
Successfully minted items. Transaction digest: ...
```

Then, in the separate terminal run the client AEA.

``` bash 
aea run
```

You will see that upon discovery the two AEAs exchange information about the transaction and the client at the end signs and sends the signature to the deployer AEA to send it to the network.

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>Transactions on Ropsten can take a significant amount of time! If you run the example a second time, and the previous transaction is still pending, it can lead to a failure.

  The warning message `Cannot verify whether transaction improves utility. Assuming it does!` can be ignored.
  </p>
</div>

## Delete the AEAs

When you're done, go up a level and delete the AEAs.
``` bash 
cd ..
aea delete erc1155_deployer
aea delete erc1155_client
```

## Communication

This diagram shows the communication between the various entities as data is successfully trustless trade. 

<div class="mermaid">
    sequenceDiagram
        participant Search
        participant Erc1155_contract
        participant Client_AEA
        participant Deployer_AEA
        participant Blockchain
    
        activate Deployer_AEA
        activate Search
        activate Client_AEA
        activate Erc1155_contract
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
        
        deactivate Deployer_AEA
        deactivate Search
        deactivate Client_AEA
        deactivate ERC1155_contract
        deactivate Blockchain
       
</div>

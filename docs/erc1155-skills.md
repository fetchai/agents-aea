The AEA `erc1155_deploy` and `erc1155_client` skills demonstrate an interaction between two AEAs with the usage of a smart contract.

* The `erc1155_deploy` skill deploys the smart contract, creates and mints items. 
* The `erc1155_client` skill signs a transaction to complete a trustless trade with the counterparty.

## Preparation instructions
 
### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

##Discussion

The scope of the specific demo is to demonstrate how to deploy a smart contract and interact with it. For the specific use-case, we create two AEAs one that deploys and creates tokens inside the smart contract and the other that signs a transaction so we can complete an atomic swap. The smart contract we are using is an ERC1155 smart contract
with a one-step atomic swap functionality. That means the trade between the two AEAs can be trustless.

####Note:
This demo serves demonstrative purposes only. Since the AEA deploying the contract also has the ability to mint tokens, 
in reality the transfer of tokens from the AEA signing the transaction is worthless.

### Launch an OEF node
In a separate terminal, launch a local OEF node (for search and discovery).
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

Keep it running for all the following demos.

## Demo: Ledger payment

A demo to run a scenario with a true ledger transaction on Ethereum `ropsten` network. This demo assumes the client
does not trust the deployer AEA to make the trade.

### Create the deployer AEA (ledger version)

Create the AEA that will deploy the contract.

``` bash
aea create my_erc1155_deploy
cd my_erc1155_deploy
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/erc1155_deploy:0.1.0
aea add contract fetchai/erc1155:0.1.0
aea install
```
Additionally, create the private key for the deployer AEA.

Generate and add a key for Ethereum use:
``` bash
aea generate-key ethereum
aea add-key ethereum eth_private_key.txt
```


### Create the client AEA (ledger version)

In another terminal, create the AEA that will sign the transaction.

``` bash
aea create my_erc1155_client
cd my_erc1155_client
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/erc1155_client:0.1.0
aea add contract fetchai/erc1155:0.1.0
aea install
```

### Update the AEA configs

Both in `my_erc1155_deploy/aea-config.yaml` and
`my_erc1155_client/aea-config.yaml`, replace `ledger_apis: {}` with the following based on the network you want to connect

Connect to Ethereum:
``` yaml
ledger_apis:
  ethereum:
    address: https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe
    chain_id: 3
    gas_price: 50
```

### Update the deployer AEA skill configs

In `my_erc1155_deploy/vendor/fetchai/skills/erc1155_deploy/skill.yaml`, update the details based on the following:
``` yaml
name: erc1155_deploy
author: fetchai
version: 0.1.0
license: Apache-2.0
fingerprint: {}
description: "The erc1155 deploy skill implements the functionality to depoly and interact with a smart contract."
contracts: ['fetchai/erc1155:0.1.0']
behaviours:
  service_registration:
    class_name: ServiceRegistrationBehaviour
    args:
      services_interval: 60
handlers:
  default:
    class_name: FIPAHandler
    args: {}
  transaction:
    class_name: TransactionHandler
    args: {}
models:
  strategy:
    class_name: Strategy
    args:
      ledger_id: 'ethereum'
      is_ledger_tx: True
      nft: 1
      ft: 2
      item_ids: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
      mint_stock: [100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
      from_supply: 10
      to_supply: 0
      value: 0
      search_schema:
        attribute_one:
          name: country
          type: str
          is_required: True
        attribute_two:
          name: city
          type: str
          is_required: True
      search_data:
        country: UK
        city: Cambridge
protocols: ['fetchai/fipa:0.1.0', 'fetchai/oef:0.1.0', 'fetchai/default:0.1.0']
ledgers: ['fetchai']
dependencies:
  vyper: { version: "==0.1.0b12"}
```
The `search_schema` and the `search_data` are used to register the service in the OEF and make your agent discoverable. The name of each attribute must be a key in the `search_data` dictionary.


### Fund the deployer AEA

To create some wealth for your deployer AEA for the Ethereum `ropsten` network. Note that this needs to be executed from deployer AEA folder:

``` bash
aea generate-wealth ethereum
```

## Run the AEAs

You can change the endpoint's address and port by modifying the connection's yaml file (my_seller_aea/connection/oef/connection.yaml)

Under config locate :

``` bash
addr: ${OEF_ADDR: 127.0.0.1}
```
and replace it with your ip (The ip of the machine that runs the oef image.)

Run both AEAs from their respective terminals. First, run the deployer and wait until it deploys and creates the items in the smart contract.
Then in a separate terminal run the client AEA. You will see that upon discovery the two AEAs exchange information about the transaction and the client at
the end signs and sends the signature to the deployer AEA to send it to the network.


``` bash 
aea run --connections fetchai/oef:0.1.0
```


## Delete the AEAs
When you're done, go up a level and delete the AEAs.
``` bash 
cd ..
aea delete my_seller_aea
aea delete my_buyer_aea
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

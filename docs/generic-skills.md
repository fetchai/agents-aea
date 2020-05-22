The AEA generic buyer and seller skills demonstrate an interaction between two AEAs.

* The provider of a service in the form of data for sale.
* The buyer of a service.

## Discussion

The scope of the specific demo is to demonstrate how to create an easy configurable AEA. The seller AEA will sell the service specified in the `skill.yaml` file and deliver it upon payment by the buyer. Adding a database or hardware sensor for loading the data is out of the scope of this demo.

As a result, the AEA can provide data that are listed in the `skill.yaml` file. This demo does not utilize a smart contract. We interact with a ledger only to complete a transaction. This demo assumes the buyer
trusts the seller AEA to send the data upon successful payment.

Moreover, this example provides a way to customise the skill code and connect a database or sensor. You can modify the `has_data_source` variable in `skill.yaml` file of the generic_seller skill to True. Then you have to implement the method `collect_from_data_source(self)` inside the strategy.py file.

## Communication

This diagram shows the communication between the various entities as data is successfully sold by the seller AEA to the buyer. 

<div class="mermaid">
    sequenceDiagram
        participant Search
        participant Buyer_AEA
        participant Seller_AEA
        participant Blockchain
    
        activate Buyer_AEA
        activate Search
        activate Seller_AEA
        activate Blockchain
        
        Seller_AEA->>Search: register_service
        Buyer_AEA->>Search: search
        Search-->>Buyer_AEA: list_of_agents
        Buyer_AEA->>Seller_AEA: call_for_proposal
        Seller_AEA->>Buyer_AEA: propose
        Buyer_AEA->>Seller_AEA: accept
        Seller_AEA->>Buyer_AEA: match_accept
        Buyer_AEA->>Blockchain: transfer_funds
        Buyer_AEA->>Seller_AEA: send_transaction_hash
        Seller_AEA->>Blockchain: check_transaction_status
        Seller_AEA->>Buyer_AEA: send_data
        
        deactivate Buyer_AEA
        deactivate Search
        deactivate Seller_AEA
        deactivate Blockchain
       
</div>

## Preparation instructions
 
### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

### Launch an OEF search and communication node
In a separate terminal, launch a local [OEF search and communication node](../oef-ledger).
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

Keep it running for all the following demos.

## Demo instructions

### Create the seller AEA

First, fetch the seller AEA:
``` bash
aea fetch fetchai/generic_seller:0.1.0 --alias my_seller_aea
cd generic_seller
aea install
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create the seller from scratch:
``` bash
aea create my_seller_aea
cd my_seller_aea
aea add connection fetchai/oef:0.3.0
aea add skill fetchai/generic_seller:0.4.0
aea install
aea config set agent.default_connection fetchai/oef:0.3.0
```

In `my_seller_aea/aea-config.yaml` replace `ledger_apis: {}` with the following based on the network you want to connect. To connect to Fetchai:
``` yaml
ledger_apis:
  fetchai:
    network: testnet
```

</p>
</details>

### Create the buyer AEA

Then, fetch the buyer AEA:
``` bash
aea fetch fetchai/generic_buyer:0.1.0 --alias my_buyer_aea
cd generic_buyer
aea install
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create the buyer from scratch:
``` bash
aea create my_buyer_aea
cd my_buyer_aea
aea add connection fetchai/oef:0.3.0
aea add skill fetchai/generic_buyer:0.3.0
aea install
aea config set agent.default_connection fetchai/oef:0.3.0
```

In `my_buyer_aea/aea-config.yaml` replace `ledger_apis: {}` with the following based on the network you want to connect. To connect to Fetchai:
``` yaml
ledger_apis:
  fetchai:
    network: testnet
```

</p>
</details>


### Generate wealth for the buyer AEA

The buyer needs to have some wealth to purchase the service from the seller.

First, create the private key for the buyer AEA based on the network you want to transact. To generate and add a private-public key pair for Fetch.ai use:
``` bash
aea generate-key fetchai
aea add-key fetchai fet_private_key.txt
```

Then, create some wealth for your buyer based on the network you want to transact with. On the Fetch.ai `testnet` network:
``` bash
aea generate-wealth fetchai
```

<details><summary>Alternatively, create wealth for other test networks.</summary>
<p>

<strong>Ledger Config:</strong>
<br>

In `my_buyer_aea/aea-config.yaml` and `my_seller_aea/aea-config.yaml` replace `ledger_apis: {}` with the following based on the network you want to connect.

To connect to Ethereum:
``` yaml
ledger_apis:
  ethereum:
    address: https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe
    chain_id: 3
    gas_price: 50
```

Alternatively, to connect to Cosmos:
``` yaml
ledger_apis:
  cosmos:
    address: http://aea-testnet.sandbox.fetch-ai.com:1317
```

<strong>Wealth:</strong>
<br>

To generate and add a private-public key pair for Ethereum use:
``` bash
aea generate-key ethereum
aea add-key ethereum eth_private_key.txt
```

On the Ethereum `ropsten` network.
``` bash
aea generate-wealth ethereum
```

Alternatively, to generate and add a private-public key pair for Cosmos use:
``` bash
aea generate-key cosmos
aea add-key cosmos cosmos_private_key.txt
```

On the Cosmos `testnet` network.
``` bash
aea generate-wealth cosmos
```

</p>
</details>


### Update the skill configs

The default skill configs assume that the transaction is settled against the fetchai ledger.

In `my_seller_aea/vendor/fetchai/skills/generi_seller/skill.yaml` the `data_for_sale` is the data the seller AEA is offering for sale.
``` yaml
models:
  ...
  strategy:
    args:
      currency_id: FET
      data_for_sale:
        pressure: 20
        temperature: 26
        wind: 10
      data_model:
        attribute_one:
          is_required: true
          name: country
          type: str
        attribute_two:
          is_required: true
          name: city
          type: str
      data_model_name: location
      has_data_source: false
      is_ledger_tx: true
      ledger_id: fetchai
      seller_tx_fee: 0
      service_data:
        city: Cambridge
        country: UK
      total_price: 10
    class_name: Strategy 
```
The `data_model`, `data_model_name` and the `service_data` are used to register the service in the [OEF search node](../oef-ledger) and make your agent discoverable. The name of each `data_model` attribute must be a key in the `service_data` dictionary.

In the generic buyer skill config (`my_buyer_aea/vendor/fetchai/skills/generic_buyer/skill.yaml`) defines the `search_query`, which has to match the `service_data` of the seller.

``` yaml
models:
  ...
  strategy:
    args:
      currency_id: FET
      is_ledger_tx: true
      ledger_id: fetchai
      max_buyer_tx_fee: 1
      max_price: 4
      search_query:
        constraint_type: ==
        search_term: country
        search_value: UK
    class_name: Strategy
```

<details><summary>Alternatively, configure skills for other test networks.</summary>
<p>

<strong>Seller:</strong>
<br>
Ensure you are in the seller project directory.

For ethereum, update the skill config of the seller via the `aea config get/set` command like so:
``` bash
aea config set vendor.fetchai.skills.generic_seller.models.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.generic_seller.models.strategy.args.ledger_id ethereum
```

Or for cosmos, like so:
``` bash
aea config set vendor.fetchai.skills.generic_seller.models.strategy.args.currency_id ATOM
aea config set vendor.fetchai.skills.generic_seller.models.strategy.args.ledger_id cosmos
```

This updates the generic seller skill config (`my_seller_aea/vendor/fetchai/skills/generic_seller/skill.yaml`).


<strong>Buyer:</strong>
<br>
Ensure you are in the buyer project directory.

For ethereum, update the skill config of the buyer via the `aea config get/set` command like so:
``` bash
aea config set vendor.fetchai.skills.generic_buyer.models.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.generic_buyer.models.strategy.args.ledger_id ethereum
```

Or for cosmos, like so:
``` bash
aea config set vendor.fetchai.skills.generic_buyer.models.strategy.args.currency_id ATOM
aea config set vendor.fetchai.skills.generic_buyer.models.strategy.args.ledger_id cosmos
```

This updates the buyer skill config (`my_buyer_aea/vendor/fetchai/skills/generic_buyer/skill.yaml`).

</p>
</details>

## Run the AEAs

Run both AEAs from their respective terminals

``` bash
aea run --connections fetchai/oef:0.3.0
```
You will see that the AEAs negotiate and then transact using the Fetch.ai testnet.

## Delete the AEAs
When you're done, go up a level and delete the AEAs.
``` bash 
cd ..
aea delete my_seller_aea
aea delete my_buyer_aea
```

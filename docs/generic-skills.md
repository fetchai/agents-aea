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
        Buyer_AEA->>Search: search_agents
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

## Demo instructions

### Create the seller AEA

First, fetch the seller AEA:
``` bash
aea fetch fetchai/generic_seller:0.13.0 --alias my_seller_aea
cd my_seller_aea
aea install
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create the seller from scratch:
``` bash
aea create my_seller_aea
cd my_seller_aea
aea add connection fetchai/p2p_libp2p:0.12.0
aea add connection fetchai/soef:0.12.0
aea add connection fetchai/ledger:0.9.0
aea add skill fetchai/generic_seller:0.16.0
aea install
aea config set agent.default_connection fetchai/p2p_libp2p:0.12.0
```

In `my_seller_aea/aea-config.yaml` add 
``` yaml
default_routing:
  fetchai/ledger_api:0.7.0: fetchai/ledger:0.9.0
  fetchai/oef_search:0.10.0: fetchai/soef:0.12.0
```

</p>
</details>

### Create the buyer AEA

Then, fetch the buyer AEA:
``` bash
aea fetch fetchai/generic_buyer:0.14.0 --alias my_buyer_aea
cd my_buyer_aea
aea install
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create the buyer from scratch:
``` bash
aea create my_buyer_aea
cd my_buyer_aea
aea add connection fetchai/p2p_libp2p:0.12.0
aea add connection fetchai/soef:0.12.0
aea add connection fetchai/ledger:0.9.0
aea add skill fetchai/generic_buyer:0.16.0
aea install
aea config set agent.default_connection fetchai/p2p_libp2p:0.12.0
```

In `my_buyer_aea/aea-config.yaml` add 
``` yaml
default_routing:
  fetchai/ledger_api:0.7.0: fetchai/ledger:0.9.0
  fetchai/oef_search:0.10.0: fetchai/soef:0.12.0
```

</p>
</details>


### Add keys for the seller AEA

First, create the private key for the seller AEA based on the network you want to transact. To generate and add a private-public key pair for Fetch.ai `AgentLand` use:
``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
aea add-key fetchai fetchai_private_key.txt --connection
```

### Add keys and generate wealth for the buyer AEA

The buyer needs to have some wealth to purchase the service from the seller.

First, create the private key for the buyer AEA based on the network you want to transact. To generate and add a private-public key pair for Fetch.ai `AgentLand` use:
``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
aea add-key fetchai fetchai_private_key.txt --connection
```

Then, create some wealth for your buyer based on the network you want to transact with. On the Fetch.ai `AgentLand` network:
``` bash
aea generate-wealth fetchai
```

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
        generic: data
      has_data_source: false
      is_ledger_tx: true
      ledger_id: fetchai
      location:
        latitude: 51.5194
        longitude: 0.127
      service_data:
        key: seller_service
        value: generic_service
      service_id: generic_service
      unit_price: 10
    class_name: GenericStrategy
```
The `data_model`, `data_model_name` and the `service_data` are used to register the service in the <a href="../simple-oef">SOEF search node</a> and make your agent discoverable. The name of each `data_model` attribute must be a key in the `service_data` dictionary.

In the generic buyer skill config (`my_buyer_aea/vendor/fetchai/skills/generic_buyer/skill.yaml`) defines the `search_query`, which has to match the `service_data` of the seller.

``` yaml
models:
  ...
  strategy:
    args:
      currency_id: FET
      is_ledger_tx: true
      ledger_id: fetchai
      location:
        latitude: 51.5194
        longitude: 0.127
      max_negotiations: 1
      max_tx_fee: 1
      max_unit_price: 20
      search_query:
        constraint_type: ==
        search_key: seller_service
        search_value: generic_service
      search_radius: 5.0
      service_id: generic_service
    class_name: GenericStrategy
```

### Update the skill configs

Both skills are abstract skills, make them instantiatable:

``` bash
cd my_seller_aea
aea config set vendor.fetchai.skills.generic_seller.is_abstract false --type bool
```

``` bash
cd my_buyer_aea
aea config set vendor.fetchai.skills.generic_buyer.is_abstract false --type bool
```

## Run the AEAs

Run both AEAs from their respective terminals.

First, run the seller AEA:

``` bash
aea run
```

Once you see a message of the form `To join its network use multiaddr: ['SOME_ADDRESS']` take note of the address.

Then, update the configuration of the buyer AEA's p2p connection (in `vendor/fetchai/connections/p2p_libp2p/connection.yaml`) replace the following:

``` yaml
config:
  delegate_uri: 127.0.0.1:11001
  entry_peers: ['SOME_ADDRESS']
  local_uri: 127.0.0.1:9001
  log_file: libp2p_node.log
  public_uri: 127.0.0.1:9001
```

where `SOME_ADDRESS` is replaced accordingly.

Then run the buyer AEA:
``` bash
aea run
```

You will see that the AEAs negotiate and then transact using the Fetch.ai testnet.

## Delete the AEAs
When you're done, go up a level and delete the AEAs.
``` bash 
cd ..
aea delete my_seller_aea
aea delete my_buyer_aea
```
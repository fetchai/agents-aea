The AEA generic buyer and seller skills demonstrate an interaction between two AEAs:

* An AEA that provides a (data selling) service.
* An AEA that demands this service.

## Discussion

The scope of this guide is demonstrating how to create easily configurable AEAs. The buyer AEA finds the seller, negotiates the terms of trade, and if successful purchases the data by sending payment. The seller AEA sells the service specified in its `skill.yaml` file, delivering it to the buyer upon receiving payment. 

Note that these agents do not utilize a smart contract but interact with a ledger to complete a transaction. Moreover, in this setup, the buyer agent has to trust the seller to send the data upon successful payment.

The corresponding packages can be customised to allow for a database or sensor to be defined from which data is loaded. This is done by first modifying the `has_data_source` variable in `skill.yaml` file of the `generic_seller` skill to `True`. Then you have to provide an implementation for the `collect_from_data_source(self)` method in the `strategy.py` file. More detailed instructions is beyond the scope of this guide.

## Communication

The following diagram shows the communication between various entities in this interaction.

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
aea fetch fetchai/generic_seller:0.28.0 --alias my_seller_aea
cd my_seller_aea
aea install
aea build
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create the seller from scratch:
``` bash
aea create my_seller_aea
cd my_seller_aea
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/ledger:0.19.0
aea add skill fetchai/generic_seller:0.27.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<2.0.0,>=1.0.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.25.0
aea config set --type dict agent.default_routing \
'{
  "fetchai/ledger_api:1.0.0": "fetchai/ledger:0.19.0",
  "fetchai/oef_search:1.0.0": "fetchai/soef:0.26.0"
}'
aea install
aea build
```

</p>
</details>

### Create the buyer AEA

Then, in another terminal fetch the buyer AEA:
``` bash
aea fetch fetchai/generic_buyer:0.29.0 --alias my_buyer_aea
cd my_buyer_aea
aea install
aea build
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create the buyer from scratch:
``` bash
aea create my_buyer_aea
cd my_buyer_aea
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/ledger:0.19.0
aea add skill fetchai/generic_buyer:0.26.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<2.0.0,>=1.0.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.25.0
aea config set --type dict agent.default_routing \
'{
  "fetchai/ledger_api:1.0.0": "fetchai/ledger:0.19.0",
  "fetchai/oef_search:1.0.0": "fetchai/soef:0.26.0"
}'
aea install
aea build
```

</p>
</details>


### Add keys for the seller AEA

Create the private key for the seller AEA based on the network you want to transact. To generate and add a private-public key pair for Fetch.ai `StargateWorld` use:
``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
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

### Add keys and generate wealth for the buyer AEA

The buyer needs to have some wealth to purchase the data from the seller.

First, create the private key for the buyer AEA based on the network you want to transact. To generate and add a private-public key pair for Fetch.ai `StargateWorld` use:
``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
```

Then, create some wealth for your buyer based on the network you want to transact with. On the Fetch.ai `StargateWorld` network:
``` bash
aea generate-wealth fetchai
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

### Update the skill configurations

The default skill configurations assume that the transaction is settled against the Fetch.ai ledger.

In the generic seller's skill configuration file (`my_seller_aea/vendor/fetchai/skills/generi_seller/skill.yaml`) the `data_for_sale` is the data the seller AEA is offering for sale. In the following case, this is a one item dictionary where key is `generic` and value is `data`.

Furthermore, the `service_data` is used to register the seller's service in the <a href="../simple-oef">SOEF search node</a> and make your agent discoverable. 
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

The generic buyer skill configuration file (`my_buyer_aea/vendor/fetchai/skills/generic_buyer/skill.yaml`) includes the `search_query` which has to match the `service_data` of the seller.

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

### Update the skill configurations

Both skills are abstract skills, make them instantiable:

``` bash
cd my_seller_aea
aea config set vendor.fetchai.skills.generic_seller.is_abstract false --type bool
```

``` bash
cd my_buyer_aea
aea config set vendor.fetchai.skills.generic_buyer.is_abstract false --type bool
```

## Run the AEAs

First, run the seller AEA:

``` bash
aea run
```

Once you see a message of the form `To join its network use multiaddr 'SOME_ADDRESS'` take note of this address. (Alternatively, use `aea get-multiaddress fetchai -c -i fetchai/p2p_libp2p:0.25.0 -u public_uri` to retrieve the address.)
This is the entry peer address for the local <a href="../acn">agent communication network</a> created by the seller.

Then, configure the buyer to connect to this same local ACN by running the following command in the buyer terminal, replacing `SOME_ADDRESS` with the value you noted above:
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

Then run the buyer AEA:

``` bash
aea run
```

You will see that the AEAs negotiate and then transact using the Fetch.ai testnet.

## Delete the AEAs

When you're done, stop the agents (`CTRL+C`), go up a level and delete the AEAs.

``` bash 
cd ..
aea delete my_seller_aea
aea delete my_buyer_aea
```
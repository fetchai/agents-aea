The AEA car-park skills demonstrate an interaction between two AEAs.

* The `carpark_detection` AEA provides information on the number of car parking spaces available in a given vicinity.
* The `carpark_client` AEA is interested in purchasing information on available car parking spaces in the same vicinity.

## Discussion

The full Fetch.ai car park AEA demo is documented in its own repo <a href="https://github.com/fetchai/carpark_agent" target="_blank">here</a>.
This demo allows you to test the AEA functionality of the car park AEA demo without the detection logic.

It demonstrates how the AEAs trade car park information.

## Communication
This diagram shows the communication between the various entities as data is successfully sold by the car park AEA to the client. 

<div class="mermaid">
    sequenceDiagram
        participant Search
        participant Car_Data_Buyer_AEA
        participant Car_Park_AEA
        participant Blockchain
    
        activate Car_Data_Buyer_AEA
        activate Search
        activate Car_Park_AEA
        activate Blockchain
        
        Car_Park_AEA->>Search: register_service
        Car_Data_Buyer_AEA->>Search: search
        Search-->>Car_Data_Buyer_AEA: list_of_agents
        Car_Data_Buyer_AEA->>Car_Park_AEA: call_for_proposal
        Car_Park_AEA->>Car_Data_Buyer_AEA: propose
        Car_Data_Buyer_AEA->>Car_Park_AEA: accept
        Car_Park_AEA->>Car_Data_Buyer_AEA: match_accept
        Car_Data_Buyer_AEA->>Blockchain: transfer_funds
        Car_Data_Buyer_AEA->>Car_Park_AEA: send_transaction_hash
        Car_Park_AEA->>Blockchain: check_transaction_status
        Car_Park_AEA->>Car_Data_Buyer_AEA: send_data
        
        deactivate Client_AEA
        deactivate Search
        deactivate Car_Park_AEA
        deactivate Blockchain
</div>

## Preparation instructions

### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

## Demo instructions

### Create car detector AEA

First, fetch the car detector AEA:
``` bash
aea fetch fetchai/car_detector:0.23.0
cd car_detector
aea install
aea build
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create the car detector from scratch:
``` bash
aea create car_detector
cd car_detector
aea add connection fetchai/p2p_libp2p:0.17.0
aea add connection fetchai/soef:0.18.0
aea add connection fetchai/ledger:0.14.0
aea add skill fetchai/carpark_detection:0.20.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<0.2.0,>=0.1.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.17.0
aea config set --type dict agent.default_routing \
'{
  "fetchai/ledger_api:0.11.0": "fetchai/ledger:0.14.0",
  "fetchai/oef_search:0.14.0": "fetchai/soef:0.18.0"
}'
aea install
aea build
```

</p>
</details>

### Create car data buyer AEA

Then, fetch the car data client AEA:
``` bash
aea fetch fetchai/car_data_buyer:0.24.0
cd car_data_buyer
aea install
aea build
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create the car data client from scratch:
``` bash
aea create car_data_buyer
cd car_data_buyer
aea add connection fetchai/p2p_libp2p:0.17.0
aea add connection fetchai/soef:0.18.0
aea add connection fetchai/ledger:0.14.0
aea add skill fetchai/carpark_client:0.21.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<0.2.0,>=0.1.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.17.0
aea config set --type dict agent.default_routing \
'{
  "fetchai/ledger_api:0.11.0": "fetchai/ledger:0.14.0",
  "fetchai/oef_search:0.14.0": "fetchai/soef:0.18.0"
}'
aea install
aea build
```


</p>
</details>

### Add keys for the car data seller AEA

First, create the private key for the car data seller AEA based on the network you want to transact. To generate and add a private-public key pair for Fetch.ai `AgentLand` use:
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

### Add keys and generate wealth for the car data buyer AEA

The buyer needs to have some wealth to purchase the service from the seller.

First, create the private key for the car data buyer AEA based on the network you want to transact. To generate and add a private-public key pair for Fetch.ai `AgentLand` use:
``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
```

Then, create some wealth for your car data buyer based on the network you want to transact with. On the Fetch.ai `AgentLand` network:
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

## Run the AEAs

Run both AEAs from their respective terminals.

First, run the car data seller AEA:

``` bash
aea run
```

Once you see a message of the form `To join its network use multiaddr 'SOME_ADDRESS'` take note of the address. (Alternatively, use `aea get-multiaddress fetchai -c -i fetchai/p2p_libp2p:0.17.0 -u public_uri` to retrieve the address.)
This is the entry peer address for the local <a href="../acn">agent communication network</a> created by the car data seller.

Then, in the car data buyer, run this command (replace `SOME_ADDRESS` with the correct value as described above):
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
This allows the car data buyer to connect to the same local agent communication network as the car data seller.

Then run the buyer AEA:
``` bash
aea run
```

You will see that the AEAs negotiate and then transact using the Fetch.ai testnet.

### Cleaning up

When you're finished, delete your AEAs:
``` bash
cd ..
aea delete car_detector
aea delete car_data_buyer
```

<br />
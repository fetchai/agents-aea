The AEA thermometer skills demonstrate an interaction between two AEAs, one purchasing temperature data from the other. 

* The provider of thermometer data (the `thermometer`).
* The buyer of thermometer data (the `thermometer_client`).

## Discussion

This demo aims to demonstrate how to create a very simple AEA with the usage of the AEA framework and a thermometer sensor. The thermometer AEA will read data from the sensor each time a client requests the data and will deliver it to the client upon payment. To keep the demo simple, we avoided the usage of a database since this would increase the complexity. As a result, the AEA can provide only one reading from the sensor. This demo does not utilise a smart contract. As a result, the ledger interaction is only for completing a transaction.

## Communication

This diagram shows the communication between the various entities as data is successfully sold by the thermometer AEA to the client AEA. 

<div class="mermaid">
    sequenceDiagram
        participant Search
        participant Client_AEA
        participant Thermometer_AEA
        participant Blockchain
    
        activate Client_AEA
        activate Search
        activate Thermometer_AEA
        activate Blockchain
        
        Thermometer_AEA->>Search: register_service
        Client_AEA->>Search: search
        Search-->>Client_AEA: list_of_agents
        Client_AEA->>Thermometer_AEA: call_for_proposal
        Thermometer_AEA->>Client_AEA: propose
        Client_AEA->>Thermometer_AEA: accept
        Thermometer_AEA->>Client_AEA: match_accept
        Client_AEA->>Blockchain: transfer_funds
        Client_AEA->>Thermometer_AEA: send_transaction_hash
        Thermometer_AEA->>Blockchain: check_transaction_status
        Thermometer_AEA->>Client_AEA: send_data
        
        deactivate Client_AEA
        deactivate Search
        deactivate Thermometer_AEA
        deactivate Blockchain
       
</div>
<br>

## Option 1: AEA Manager approach

Follow this approach when using the AEA Manager Desktop app. Otherwise, skip and follow the CLI approach below. 

### Preparation instructions

Install the <a href="https://aea-manager.fetch.ai" target="_blank">AEA Manager</a>.

### Demo instructions

The following steps assume you have launched the AEA Manager Desktop app.

1. Add a new AEA called `my_thermometer_aea` with public id `fetchai/thermometer_aea:0.29.0`.

2. Add another new AEA called `my_thermometer_client` with public id `fetchai/thermometer_client:0.30.0`.

3. Copy the address from the `my_thermometer_client` into your clip board. Then go to the <a href="https://explore-stargateworld.fetch.ai" target="_blank">StargateWorld block explorer</a> and request some test tokens via `Get Funds`.

4. Run the `my_thermometer_aea` AEA. Navigate to its logs and copy the multiaddress displayed.

5. Navigate to the settings of the `my_thermometer_client` and under `components > connection >` `fetchai/p2p_libp2p:0.22.0` update as follows (make sure to replace the placeholder with the multiaddress):
``` bash
{
  "delegate_uri": "127.0.0.1:11001",
  "entry_peers": ["REPLACE_WITH_MULTI_ADDRESS_HERE"],
  "local_uri": "127.0.0.1:9001",
  "log_file": "libp2p_node.log",
  "public_uri": "127.0.0.1:9001"
}
```

6. Run the `my_thermometer_client`.

In the AEA's logs, you should see the agent trading successfully.
<br>

## Option 2: CLI approach

Follow this approach when using the `aea` CLI.

### Preparation instructions
 
#### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

### Demo instructions

A demo to run the thermometer scenario with a true ledger transaction This demo assumes the buyer trusts the seller AEA to send the data upon successful payment.

#### Create thermometer AEA

First, fetch the thermometer AEA:
``` bash
aea fetch fetchai/thermometer_aea:0.29.0 --alias my_thermometer_aea
cd my_thermometer_aea
aea install
aea build
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create the thermometer AEA from scratch:
``` bash
aea create my_thermometer_aea
cd my_thermometer_aea
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/ledger:0.19.0
aea add skill fetchai/thermometer:0.26.0
aea install
aea build
aea config set agent.default_connection fetchai/p2p_libp2p:0.25.0
aea config set --type dict agent.default_routing \
'{
  "fetchai/ledger_api:1.0.0": "fetchai/ledger:0.19.0",
  "fetchai/oef_search:1.0.0": "fetchai/soef:0.26.0"
}'
```

</p>
</details>

#### Create thermometer client

Then, fetch the thermometer client AEA:
``` bash
aea fetch fetchai/thermometer_client:0.30.0 --alias my_thermometer_client
cd my_thermometer_client
aea install
aea build
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create the thermometer client from scratch:
``` bash
aea create my_thermometer_client
cd my_thermometer_client
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/ledger:0.19.0
aea add skill fetchai/thermometer_client:0.25.0
aea install
aea build
aea config set agent.default_connection fetchai/p2p_libp2p:0.25.0
aea config set --type dict agent.default_routing \
'{
  "fetchai/ledger_api:1.0.0": "fetchai/ledger:0.19.0",
  "fetchai/oef_search:1.0.0": "fetchai/soef:0.26.0"
}'
```

</p>
</details>

#### Add keys for the thermometer AEA

First, create the private key for the thermometer AEA based on the network you want to transact. To generate and add a private-public key pair for Fetch.ai `StargateWorld` use:
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

#### Add keys and generate wealth for the thermometer client AEA

The thermometer client needs to have some wealth to purchase the thermometer information.

First, create the private key for the thermometer client AEA based on the network you want to transact. To generate and add a private-public key pair for Fetch.ai use:
``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
```

Then, create some wealth for your thermometer client based on the network you want to transact with. On the Fetch.ai `testnet` network:
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

#### Run both AEAs

Run both AEAs from their respective terminals.

First, run the thermometer AEA:

``` bash
aea run
```

Once you see a message of the form `To join its network use multiaddr 'SOME_ADDRESS'` take note of the address. (Alternatively, use `aea get-multiaddress fetchai -c -i fetchai/p2p_libp2p:0.25.0 -u public_uri` to retrieve the address.) This is the entry peer address for the local <a href="../acn">agent communication network</a> created by the thermometer AEA.

Then, in the thermometer client, run this command (replace `SOME_ADDRESS` with the correct value as described above):
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
This allows the thermometer client to connect to the same local agent communication network as the thermometer AEA.

Then run the thermometer client AEA:
``` bash
aea run
```

You can see that the AEAs find each other, negotiate and eventually trade.

#### Cleaning up

When you're done, go up a level and delete the AEAs.

``` bash
cd ..
aea delete my_thermometer_aea
aea delete my_thermometer_client
```

<br />
The AEA weather skills demonstrate an interaction between two AEAs.

* The provider of weather data (the `weather_station`).
* The buyer of weather data (the `weather_client`).

## Discussion

The scope of the specific demo is to demonstrate how to create a simple AEA with the usage of the AEA framework and a database. The `weather_station` AEA
will read data from the database, that is populated with readings from a weather station, based on the requested dates and will deliver the data to the client upon payment.
This demo does not utilize a smart contract. As a result, we interact with a ledger only to complete a transaction.

You can use this AEA as an example of how to read data from a database and advertise these to possible clients.  

## Communication

This diagram shows the communication between the various entities as data is successfully sold by the weather station AEA to the client. 

<div class="mermaid">
    sequenceDiagram
        participant Search
        participant Client_AEA
        participant Weather_AEA
        participant Blockchain
    
        activate Client_AEA
        activate Search
        activate Weather_AEA
        activate Blockchain
        
        Weather_AEA->>Search: register_service
        Client_AEA->>Search: search
        Search-->>Client_AEA: list_of_agents
        Client_AEA->>Weather_AEA: call_for_proposal
        Weather_AEA->>Client_AEA: propose
        Client_AEA->>Weather_AEA: accept
        Weather_AEA->>Client_AEA: match_accept
        Client_AEA->>Blockchain: transfer_funds
        Client_AEA->>Weather_AEA: send_transaction_hash
        Weather_AEA->>Blockchain: check_transaction_status
        Weather_AEA->>Client_AEA: send_data
        
        deactivate Client_AEA
        deactivate Search
        deactivate Weather_AEA
        deactivate Blockchain
       
</div>
<br>

## Option 1: AEA Manager approach

Follow this approach when using the AEA Manager Desktop app. Otherwise, skip and follow the CLI approach below. 

### Preparation instructions

Install the <a href="https://aea-manager.fetch.ai" target="_blank">AEA Manager</a>.

### Demo instructions

The following steps assume you have launched the AEA Manager Desktop app.

1. Add a new AEA called `my_weather_station` with public id `fetchai/weather_station:0.31.0`.

2. Add another new AEA called `my_weather_client` with public id `fetchai/weather_client:0.32.0`.

3. Copy the address from the `my_weather_client` into your clip board. Then go to the <a href="https://explore-stargateworld.fetch.ai" target="_blank">StargateWorld block explorer</a> and request some test tokens via `Get Funds`.

4. Run the `my_weather_station` AEA. Navigate to its logs and copy the multiaddress displayed.

5. Navigate to the settings of the `my_weather_client` and under `components > connection >` `fetchai/p2p_libp2p:0.22.0` update as follows (make sure to replace the placeholder with the multiaddress):
``` bash
{
  "delegate_uri": "127.0.0.1:11001",
  "entry_peers": ["REPLACE_WITH_MULTI_ADDRESS_HERE"],
  "local_uri": "127.0.0.1:9001",
  "log_file": "libp2p_node.log",
  "public_uri": "127.0.0.1:9001"
}
```

6. Run the `my_weather_client`.

In the AEA's logs, you should see the agent trading successfully.
<br>

## Option 2: CLI approach

Follow this approach when using the `aea` CLI.

### Preparation instructions

#### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

### Demo instructions:

A demo to run the same scenario but with a true ledger transaction on Fetch.ai `testnet` or Ethereum `ropsten` network. This demo assumes the buyer
trusts the seller AEA to send the data upon successful payment.

#### Create the weather station

First, fetch the AEA that will provide weather measurements:
``` bash
aea fetch fetchai/weather_station:0.31.0 --alias my_weather_station
cd my_weather_station
aea install
aea build
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create the weather station from scratch:
``` bash
aea create my_weather_station
cd my_weather_station
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/ledger:0.19.0
aea add skill fetchai/weather_station:0.26.0
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


#### Create the weather client

In another terminal, fetch the AEA that will query the weather station:
``` bash
aea fetch fetchai/weather_client:0.32.0 --alias my_weather_client
cd my_weather_client
aea install
aea build
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create the weather client from scratch:
``` bash
aea create my_weather_client
cd my_weather_client
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/ledger:0.19.0
aea add skill fetchai/weather_client:0.25.0
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


#### Add keys for the weather station AEA

First, create the private key for the weather station AEA based on the network you want to transact. To generate and add a private-public key pair for Fetch.ai `StargateWorld` use:
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

#### Add keys and generate wealth for the weather client AEA

The weather client needs to have some wealth to purchase the service from the weather station.

First, create the private key for the weather client AEA based on the network you want to transact. To generate and add a private-public key pair for Fetch.ai `StargateWorld` use:
``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
```

Then, create some wealth for your weather client based on the network you want to transact with. On the Fetch.ai `StargateWorld` network:
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

#### Run the AEAs

Run both AEAs from their respective terminals.

First, run the weather station AEA:

``` bash
aea run
```

Once you see a message of the form `To join its network use multiaddr 'SOME_ADDRESS'` take note of the address. (Alternatively, use `aea get-multiaddress fetchai -c -i fetchai/p2p_libp2p:0.25.0 -u public_uri` to retrieve the address.) This is the entry peer address for the local <a href="../acn">agent communication network</a> created by the weather station.

Then, in the weather client, run this command (replace `SOME_ADDRESS` with the correct value as described above):
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
This allows the weather client to connect to the same local agent communication network as the weather station.

Then run the weather client AEA:
``` bash
aea run
```

You will see that the AEAs negotiate and then transact using the selected ledger.

#### Cleaning up

When you're done, go up a level and delete the AEAs.

``` bash
cd ..
aea delete my_weather_station
aea delete my_weather_client
```

<br />
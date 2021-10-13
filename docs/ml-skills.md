The AEA ML (machine learning) skills demonstrate an interaction between two AEAs, one purchasing data from the other and training a machine learning model with it. 

There are two types of AEAs:

* The `ml_data_provider` which sells training data.
* The `ml_model_trainer` which purchases data and trains a model

## Discussion

This demo aims to demonstrate the integration of a simple AEA with machine learning using the AEA framework. The `ml_data_provider` AEA provides some sample data and delivers to the client upon payment. 
Once the client receives the data, it trains a model. This process can be found in `tasks.py`.
This demo does not utilize a smart contract. As a result, the ledger interaction is only for completing a transaction.

Since the AEA framework enables using third-party libraries from PyPI, we can directly reference any external dependencies.
The `aea install` command installs all dependencies an AEA needs that is listed in one of its skills' YAML file. 

## Communication

This diagram shows the communication between the two AEAs.

<div class="mermaid">
    sequenceDiagram
        participant ml_model_trainer
        participant ml_data_provider
        participant Search
        participant Ledger
    
        activate ml_model_trainer
        activate ml_data_provider
        activate Search
        activate Ledger
        
        ml_data_provider->>Search: register_service
        ml_model_trainer->>Search: search
        Search-->>ml_model_trainer: list_of_agents
        ml_model_trainer->>ml_data_provider: call_for_terms
        ml_data_provider->>ml_model_trainer: terms
        ml_model_trainer->>Ledger: request_transaction
        ml_model_trainer->>ml_data_provider: accept (incl transaction_hash)
        ml_data_provider->>Ledger: check_transaction_status
        ml_data_provider->>ml_model_trainer: data
        loop train
            ml_model_trainer->>ml_model_trainer: tran_model
        end
        
        deactivate ml_model_trainer
        deactivate ml_data_provider
        deactivate Search
        deactivate Ledger

</div>
<br>

## Option 1: AEA Manager approach

Follow this approach when using the AEA Manager Desktop app. Otherwise, skip and follow the CLI approach below. 

### Preparation instructions

Install the <a href="https://aea-manager.fetch.ai" target="_blank">AEA Manager</a>.

### Demo instructions

The following steps assume you have launched the AEA Manager Desktop app.

1. Add a new AEA called `ml_data_provider` with public id `fetchai/ml_data_provider:0.28.0`.

2. Add another new AEA called `ml_model_trainer` with public id `fetchai/ml_model_trainer:0.29.0`.

3. Copy the address from the `ml_model_trainer` into your clip board. Then go to the <a href="https://explore-stargateworld.fetch.ai" target="_blank">StargateWorld block explorer</a> and request some test tokens via `Get Funds`.

4. Run the `ml_data_provider` AEA. Navigate to its logs and copy the multiaddress displayed.

5. Navigate to the settings of the `ml_model_trainer` and under `components > connection >` `fetchai/p2p_libp2p:0.22.0` update as follows (make sure to replace the placeholder with the multiaddress):
``` bash
{
  "delegate_uri": "127.0.0.1:11001",
  "entry_peers": ["REPLACE_WITH_MULTI_ADDRESS_HERE"],
  "local_uri": "127.0.0.1:9001",
  "log_file": "libp2p_node.log",
  "public_uri": "127.0.0.1:9001"
}
```

6. Run the `ml_model_trainer`.

In the AEA's logs, you should see the agents trading successfully, and the training agent training its machine learning model using the data purchased. 
The trainer keeps purchasing data and training its model until stopped.  
<br>

## Option 2: CLI approach

Follow this approach when using the `aea` CLI.

### Preparation instructions

#### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

### Demo instructions

#### Create data provider AEA

First, fetch the data provider AEA:
``` bash
aea fetch fetchai/ml_data_provider:0.31.0
cd ml_data_provider
aea install
aea build
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create the data provider from scratch:
``` bash
aea create ml_data_provider
cd ml_data_provider
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/ledger:0.19.0
aea add skill fetchai/ml_data_provider:0.26.0
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

#### Create model trainer AEA

Then, fetch the model trainer AEA:
``` bash
aea fetch fetchai/ml_model_trainer:0.32.0
cd ml_model_trainer
aea install
aea build
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create the model trainer from scratch:
``` bash
aea create ml_model_trainer
cd ml_model_trainer
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/ledger:0.19.0
aea add skill fetchai/ml_train:0.28.0
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

#### Add keys for the data provider AEA

First, create the private key for the data provider AEA based on the network you want to transact. To generate and add a private-public key pair for Fetch.ai `StargateWorld` use:
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

#### Add keys and generate wealth for the model trainer AEA

The model trainer needs to have some wealth to purchase the data from the data provider.

First, create the private key for the model trainer AEA based on the network you want to transact. To generate and add a private-public key pair for Fetch.ai `StargateWorld` use:
``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
```

Then, create some wealth for your model trainer based on the network you want to transact with. On the Fetch.ai `StargateWorld` network:
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

First, run the data provider AEA:

``` bash
aea run
```

Once you see a message of the form `To join its network use multiaddr 'SOME_ADDRESS'` take note of the address. (Alternatively, use `aea get-multiaddress fetchai -c -i fetchai/p2p_libp2p:0.25.0 -u public_uri` to retrieve the address.)
This is the entry peer address for the local <a href="../acn">agent communication network</a> created by the ML data provider.

<!--
Then, in the model trainer, update the configuration of the model trainer AEA's p2p connection by appending the following YAML text at the end of the `aea-config.yaml` file:

``` yaml
---
public_id: fetchai/p2p_libp2p:0.25.0
type: connection
config:
  delegate_uri: 127.0.0.1:11001
  entry_peers:
  - SOME_ADDRESS
  local_uri: 127.0.0.1:9001
  log_file: libp2p_node.log
  public_uri: 127.0.0.1:9001
```

where `SOME_ADDRESS` is replaced with the appropriate value.
-->
Then, in the ML model trainer, run this command (replace `SOME_ADDRESS` with the correct value as described above):
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
This allows the model trainer to connect to the same local agent communication network as the data provider.


Then run the model trainer AEA:
``` bash
aea run
```

You can see that the AEAs find each other, negotiate and eventually trade. After the trade, the model trainer AEA trains its ML model using the data it has purchased. 
This AEA keeps purchasing data and training its model until stopped.

#### Cleaning up

When you're finished, delete your AEAs:
``` bash
cd ..
aea delete ml_data_provider
aea delete ml_model_trainer
```

<br />
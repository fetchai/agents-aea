The AEA ML (machine learning) skills demonstrate an interaction between two AEAs trading data.

There are two types of AEAs:

* The `ml_data_provider` which sells training data.
* The `ml_model_trainer` which trains a model

## Discussion

The scope of the specific demo is to demonstrate how to create a simple AEA with integration of machine learning, and the usage of the AEA framework. The `ml_data_provider` AEA
will provide some sample data and will deliver to the client upon payment. Once the client gets the data, it will train the model. The process can be found in the `tasks.py` file.
This demo does not utilize a smart contract. As a result, we interact with a ledger only to complete a transaction.

Since the AEA framework enables us to use third-party libraries hosted on PyPI we can directly reference the external dependencies.
The `aea install` command will install each dependency that the specific AEA needs and is listed in the skill's YAML file. 

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

## Preparation instructions

### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

## Demo instructions

### Create data provider AEA

First, fetch the data provider AEA:
``` bash
aea fetch fetchai/ml_data_provider:0.23.0
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
aea add connection fetchai/p2p_libp2p:0.17.0
aea add connection fetchai/soef:0.18.0
aea add connection fetchai/ledger:0.14.0
aea add skill fetchai/ml_data_provider:0.20.0
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

### Create model trainer AEA

Then, fetch the model trainer AEA:
``` bash
aea fetch fetchai/ml_model_trainer:0.24.0
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
aea add connection fetchai/p2p_libp2p:0.17.0
aea add connection fetchai/soef:0.18.0
aea add connection fetchai/ledger:0.14.0
aea add skill fetchai/ml_train:0.22.0
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

### Add keys for the data provider AEA

First, create the private key for the data provider AEA based on the network you want to transact. To generate and add a private-public key pair for Fetch.ai `AgentLand` use:
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

### Add keys and generate wealth for the model trainer AEA

The model trainer needs to have some wealth to purchase the data from the data provider.

First, create the private key for the model trainer AEA based on the network you want to transact. To generate and add a private-public key pair for Fetch.ai `AgentLand` use:
``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
```

Then, create some wealth for your model trainer based on the network you want to transact with. On the Fetch.ai `AgentLand` network:
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

### Run both AEAs

Run both AEAs from their respective terminals.

First, run the data provider AEA:

``` bash
aea run
```

Once you see a message of the form `To join its network use multiaddr 'SOME_ADDRESS'` take note of the address. (Alternatively, use `aea get-multiaddress fetchai -c -i fetchai/p2p_libp2p:0.17.0 -u public_uri` to retrieve the address.)
This is the entry peer address for the local <a href="../acn">agent communication network</a> created by the ML data provider.

<!--
Then, in the model trainer, update the configuration of the model trainer AEA's p2p connection by appending the following YAML text at the end of the `aea-config.yaml` file:

``` yaml
---
public_id: fetchai/p2p_libp2p:0.17.0
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

You can see that the AEAs find each other, negotiate and eventually trade.

### Cleaning up

When you're finished, delete your AEAs:
``` bash
cd ..
aea delete ml_data_provider
aea delete ml_model_trainer
```

<br />
The AEA ML (machine learning) skills demonstrate an interaction between two AEAs trading data.

There are two types of AEAs:

* The `ml_data_provider` which sells training data.
* The `ml_model_trainer` which trains a model

## Discussion

The scope of the specific demo is to demonstrate how to create a simple AEA with integration of machine learning, and the usage of the AEA framework. The ml_data_provider AEA
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

### Launch an OEF search and communication node

In a separate terminal, launch a local [OEF search and communication node](../oef-ledger).
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

Keep it running for the following demo.

## Demo instructions

### Create data provider AEA

First, fetch the data provider AEA:
``` bash
aea fetch fetchai/ml_data_provider:0.5.0
cd ml_data_provider
aea install
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create the data provider from scratch:
``` bash
aea create ml_data_provider
cd ml_data_provider
aea add connection fetchai/oef:0.4.0
aea add skill fetchai/ml_data_provider:0.4.0
aea config set agent.default_connection fetchai/oef:0.4.0
aea install
```

In `ml_data_provider/aea-config.yaml` replace `ledger_apis: {}` with the following based on the network you want to connect. To connect to Fetchai:
``` yaml
ledger_apis:
  fetchai:
    network: testnet
```

</p>
</details>

### Create model trainer AEA

Then, fetch the model trainer AEA:
``` bash
aea fetch fetchai/ml_model_trainer:0.5.0
cd ml_model_trainer
aea install
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create the model trainer from scratch:
``` bash
aea create ml_model_trainer
cd ml_model_trainer
aea add connection fetchai/oef:0.4.0
aea add skill fetchai/ml_train:0.4.0
aea config set agent.default_connection fetchai/oef:0.4.0
aea install
```

In `ml_model_trainer/aea-config.yaml` replace `ledger_apis: {}` with the following based on the network you want to connect.

To connect to Fetchai:
``` yaml
ledger_apis:
  fetchai:
    network: testnet
```

</p>
</details>

### Generate wealth for the model trainer AEA

The model trainer needs to have some wealth to purchase the training data.

First, create the private key for the model trainer AEA based on the network you want to transact. To generate and add a private-public key pair for Fetch.ai use:
``` bash
aea generate-key fetchai
aea add-key fetchai fet_private_key.txt
```

Then, create some wealth for your model trainer based on the network you want to transact with. On the Fetch.ai `testnet` network:
``` bash
aea generate-wealth fetchai
```

<details><summary>Alternatively, create wealth for other test networks.</summary>
<p>

<strong>Ledger Config:</strong>
<br>

In `ml_model_trainer/aea-config.yaml` and `ml_data_provider/aea-config.yaml` replace `ledger_apis: {}` with the following based on the network you want to connect.

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

<details><summary>Alternatively, configure skills for other test networks.</summary>
<p>

<strong>Data provider:</strong>
<br>
Ensure you are in the ml_data_provider project directory.

For ethereum, update the skill config of the data provider via the `aea config get/set` command like so:
``` bash
aea config set vendor.fetchai.skills. ml_data_provider.models.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.ml_data_provider.models.strategy.args.ledger_id ethereum
```

Or for cosmos, like so:
``` bash
aea config set vendor.fetchai.skills.ml_data_provider.models.strategy.args.currency_id ATOM
aea config set vendor.fetchai.skills.ml_data_provider.models.strategy.args.ledger_id cosmos
```

This updates the ml_data_provider skill config (`ml_data_provider/vendor/fetchai/skills/ml_data_provider/skill.yaml`).


<strong>Model trainer:</strong>
<br>
Ensure you are in the ml_model_trainer project directory.

For ethereum, update the skill config of the ml_model_trainer via the `aea config get/set` command like so:
``` bash
aea config set vendor.fetchai.skills.ml_trainer.models.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.ml_trainer.models.strategy.args.ledger_id ethereum
```

Or for cosmos, like so:
``` bash
aea config set vendor.fetchai.skills.ml_train.models.strategy.args.currency_id ATOM
aea config set vendor.fetchai.skills.ml_train.models.strategy.args.ledger_id cosmos
```

This updates the ml_nodel_trainer skill config (`ml_model_trainer/vendor/fetchai/skills/ml_train/skill.yaml`).

</p>
</details>

### Run both AEAs

Finally, run both AEAs from their respective directories:
``` bash
aea run --connections fetchai/oef:0.4.0
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

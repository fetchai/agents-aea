The AEA ML (machine learning) skills demonstrate an interaction between two AEAs trading data.

There are two types of AEAs:

* The `ml_data_provider` which sells training data.
* The `ml_model_trainer` which trains a model

### Discussion

The scope of the specific demo is to demonstrate how to create a simple AEA with integration of machine learning, and the usage of the AEA framework. The ml_data_provider AEA
will provide some sample data and will deliver to the client upon payment. Once the client gets the data, it will train the model. The process can be found in the `tasks.py` file.
This demo does not utilize a smart contract. As a result, we interact with a ledger only to complete a transaction.

Since the AEA framework enables us to use third-party libraries hosted on PyPI we can directly reference the external dependencies.
The `aea install` command will install each dependency that the specific AEA needs and is listed in the skill's YAML file. 

## Preparation instructions

### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

### Launch an OEF search and communication node

In a separate terminal, launch a local [OEF search and communication node](../oef-ledger).
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

Keep it running for all the following demos.

## Demo instructions 1 - no ledger payment:

### Create the data provider AEA

Create the AEA that will provide the data.

``` bash
aea create ml_data_provider
cd ml_data_provider
aea add connection fetchai/oef:0.2.0
aea add skill fetchai/ml_data_provider:0.2.0
aea config set agent.default_connection fetchai/oef:0.2.0
```

### Alternatively, install the AEA directly

In the root directory, fetch the data provider AEA and enter the project.
``` bash
aea fetch fetchai/ml_data_provider:0.3.0
cd ml_data_provider
```
The `aea fetch` command creates the entire AEA, including its dependencies for you.

### Install the dependencies

The ml data provider uses `tensorflow` and `numpy`.
``` bash
aea install
```

### Run the data provider AEA

``` bash
aea run --connections fetchai/oef:0.2.0
```

### Create the model trainer AEA

In a separate terminal, in the root directory, create the model trainer AEA.

``` bash
aea create ml_model_trainer
cd ml_model_trainer
aea add connection fetchai/oef:0.2.0
aea add skill fetchai/ml_train:0.2.0
aea config set agent.default_connection fetchai/oef:0.2.0
```

### Alternatively, install the AEA directly

In the root directory, fetch the data provider AEA and enter the project.
``` bash
aea fetch fetchai/ml_model_trainer:0.3.0
cd ml_model_trainer
```

### Install the dependencies

The ml data provider uses `tensorflow` and `numpy`.
``` bash
aea install
```

### Run the model trainer AEA

``` bash
aea run --connections fetchai/oef:0.2.0
```

After some time, you should see the AEAs transact and the model trainer train its model.


## Demo instructions - Ledger payment:

We will now run the same demo but with a real ledger transaction on Fetch.ai or Ethereum `ropsten` network. This demo assumes the buyer
trusts the seller AEA to send the data upon successful payment.

### Create the data provider AEA

Create the AEA that will provide the data.

``` bash
aea create ml_data_provider
cd ml_data_provider
aea add connection fetchai/oef:0.2.0
aea add skill fetchai/ml_data_provider:0.2.0
aea install
aea config set agent.default_connection fetchai/oef:0.2.0
```

### Create the model trainer AEA

In a separate terminal, in the root directory, create the model trainer AEA.

``` bash
aea create ml_model_trainer
cd ml_model_trainer
aea add connection fetchai/oef:0.2.0
aea add skill fetchai/ml_train:0.2.0
aea install
aea config set agent.default_connection fetchai/oef:0.2.0
```

Additionally, create the private key for the model trainer AEA based on the network you want to transact.

To generate and add a key for Fetch.ai use:
``` bash
aea generate-key fetchai
aea add-key fetchai fet_private_key.txt
```

To generate and add a key for Ethereum use:
``` bash
aea generate-key ethereum
aea add-key ethereum eth_private_key.txt
```

### Update the AEA configs

Both in `ml_model_trainer/aea-config.yaml` and
`ml_data_provider/aea-config.yaml`, replace `ledger_apis: {}` with the following based on the network you want to connect.

To connect to Fetchai:
``` yaml
ledger_apis:
  fetchai:
    network: testnet
```

To connect to Ethereum:
``` yaml
ledger_apis:
  ethereum:
    address: https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe
    chain_id: 3
    gas_price: 50
```

### Fund the ml model trainer AEA

Create some wealth for your ml model trainer based on the network you want to transact with: 

On the Fetch.ai `testnet` network.
``` bash
aea generate-wealth fetchai
```

On the Ethereum `ropsten` . (It takes a while).
``` bash
aea generate-wealth ethereum
```

### Update the skill configs

In the ml data provider skill config (`ml_data_provider/skills/ml_data_provider/skill.yaml`) under strategy, amend the `currency_id` and `ledger_id` as follows.

``` yaml
|----------------------------------------------------------------------|
|         FETCHAI                   |           ETHEREUM               |
|-----------------------------------|----------------------------------|
|models:                            |models:                           |              
|  strategy:                        |  strategy:                       |
|     class_name: Strategy          |     class_name: Strategy         |
|    args:                          |    args:                         |
|      price_per_data_batch: 100    |      price_per_data_batch: 100   |
|      batch_size: 2                |      batch_size: 2               |
|      seller_tx_fee: 0             |      seller_tx_fee: 0            |
|      buyer_tx_fee: 10             |      buyer_tx_fee: 10            |
|      dataset_id: 'fmnist'         |      dataset_id: 'fmnist'        |
|      currency_id: 'FET'           |      currency_id: 'ETH'          |
|      ledger_id: 'fetchai'         |      ledger_id: 'ethereum'       |
|----------------------------------------------------------------------| 
```

Another way to update the skill config is via the `aea config get/set` command.
``` bash
aea config set vendor.fetchai.skills.ml_data_provider.models.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.ml_data_provider.models.strategy.args.ledger_id ethereum
```


In the ml model trainer skill config (`ml_model_trainer/skills/ml_train/skill.yaml`) under strategy, amend the `currency_id` and `ledger_id` as follows.

``` yaml
|----------------------------------------------------------------------|
|         FETCHAI                   |           ETHEREUM               |
|-----------------------------------|----------------------------------|
|models:                            |models:                           |              
|  strategy:                        |  strategy:                       |
|     class_name: Strategy          |     class_name: Strategy         |
|    args:                          |    args:                         |
|      dataset_id: 'fmnist'         |      dataset_id: 'fmnist'        |
|      max_unit_price: 70           |      max_unit_price: 70          |
|      max_buyer_tx_fee: 20         |      max_buyer_tx_fee: 20        |
|      currency_id: 'FET'           |      currency_id: 'ETH'          |
|      ledger_id: 'fetchai'         |      ledger_id: 'ethereum'       |
|      is_ledger_tx: True           |      is_ledger_tx: True          |
|----------------------------------------------------------------------| 
```

Another way to update the skill config is via the `aea config get/set` command.
``` bash
aea config set vendor.fetchai.skills.ml_train.models.strategy.args.max_buyer_tx_fee 10000 --type int
aea config set vendor.fetchai.skills.ml_train.models.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.ml_train.models.strategy.args.ledger_id ethereum
aea config set vendor.fetchai.skills.ml_train.models.strategy.args.is_ledger_tx True --type bool
```


### Run both AEAs

From their respective directories, run both AEAs
``` bash
aea run --connections fetchai/oef:0.2.0
```

### Clean up
``` bash
cd ..
aea delete ml_data_provider
aea delete ml_model_trainer
```

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


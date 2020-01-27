The AEA ml skills demonstrate an interaction between two AEAs trading data.

There are two types of AEAs:

* The ml data provider which sells training data.
* The ml model trainer which trains a model

## Preparation instructions

### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.


### Launch an OEF node
In a separate terminal, launch a local OEF node (for search and discovery).
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

Keep it running for all the following demos.

## Demo instructions 1 - no ledger payment:


### Create the data provider AEA
In the root directory, create the data provider AEA and enter the project.
``` bash
aea create ml_data_provider
cd ml_data_provider
```

Add the `ml_data_provider` skill and `oef` connection.
``` bash
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/ml_data_provider:0.1.0
```

### Alternatively, install the AEA directly
In the root directory, fetch the data provider AEA and enter the project.
``` bash
aea fetch fetchai/ml_data_provider:0.1.0
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
aea run --connections fetchai/oef:0.1.0
```

### Create the model trainer AEA
In a separate terminal, in the root directory, create the model trainer AEA and enter the project.
``` bash
aea create ml_model_trainer
cd ml_model_trainer
```

Add the `ml_train` skill and `oef` connection.
``` bash
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/ml_train:0.1.0
```

### Alternatively, install the AEA directly
In the root directory, fetch the data provider AEA and enter the project.
``` bash
aea fetch fetchai/ml_model_trainer:0.1.0
cd ml_model_trainer
```

### Install the dependencies
The ml data provider uses `tensorflow` and `numpy`.
``` bash
aea install
```

### Run the model trainer AEA
``` bash
aea run --connections fetchai/oef:0.1.0
```

After some time, you should see the AEAs transact and the model trainer train its model.


## Demo instructions 2 - Fetch.ai ledger payment:


We will now run the same demo but with a real ledger transaction on Fetch.ai test net.

### Update the AEA configs

Both in `ml_model_trainer/aea-config.yaml` and
`ml_data_provider/aea-config.yaml`, replace `ledger_apis: {}` with the following.

``` yaml
ledger_apis:
  fetchai:
    network: testnet
```

### Fund the ml model trainer AEA

Create some wealth for your ml model trainer on the Fetch.ai `testnet`. (It takes a while).
``` bash
aea generate-wealth fetchai
```

### Update the ml model trainer AEA skills config

We tell the ml model trainer skill to use the ledger, by using the following command:
``` bash
aea config set vendor.fetchai.skills.ml_train.shared_classes.strategy.args.is_ledger_tx True --type bool
```

### Run both AEAs

From their respective directories, run both AEAs
``` bash
aea run --connections fetchai/oef:0.1.0
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


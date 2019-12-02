The AEA ml skills demonstrate an interaction between two AEAs trading data.

There are two types of agents:

* The ml data provider which sells training data.
* The ml model trainer which trains a model

### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.


## Launch an OEF node
In a separate terminal, launch a local OEF node (for search and discovery).
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

Keep it running for all the following demos.

## Demo:


### Create the data provider AEA
In the root directory, create the data provider AEA.
``` bash
aea create ml_data_provider
```

### Add the `ml_data_provider` skill
``` bash
cd ml_data_provider
aea add skill ml_data_provider
```

### Install the dependencies
``` bash
aea install
```

### Run the data provider AEA
``` bash
aea run
```

### Create the model trainer AEA
In a separate terminal, in the root directory, create the model trainer AEA.
``` bash
aea create ml_model_trainer
```

### Add the `ml_train` skill to the model trainer AEA
``` bash
cd ml_model_trainer
aea add skill ml_train
```

### Run the model trainer AEA
``` bash
aea run
```

### Clean up
``` bash
cd ..
aea delete ml_data_provider
aea delete ml_model_trainer
```


### Communication
This diagram shows the communication between the two agents.

<div class="mermaid">
    sequenceDiagram
        participant ml_model_trainer
        participant ml_data_provider
        participant OEF
        participant Ledger
    
        activate ml_model_trainer
        activate ml_data_provider
        activate OEF
        activate Ledger
        
        ml_model_trainer->>OEF: search
        OEF-->>ml_model_trainer: list_of_agents
        ml_model_trainer->>ml_data_provider: call_for_terms
        ml_data_provider->>ml_model_trainer: terms
        ml_model_trainer->>Ledger: request_transaction
        ml_model_trainer->>ml_data_provider: accept (incl transaction_hash)
        ml_data_provider->>Ledger: check_transaction_status
        ml_data_provider->>ml_model_trainer: data
        
        deactivate ml_model_trainer
        deactivate ml_data_provider
        deactivate OEF
        deactivate Ledger

</div>  


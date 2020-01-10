The full Fetch.ai car park agent demo is documented in its own repo [here](https://github.com/fetchai/carpark_agent).

This demo allows you to test the AEA functionality of the car park agent demo without the detection logic.

It demonstrates how the agents trade car park information.


## Preparation instructions

### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

### Launch the OEF

In a separate terminal, launch a local OEF node (for search and discovery).
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

Keep it running for all the following.


## Demo instructions

### Create carpark detection agent

First, create the carpark detection agent:
``` bash
aea create car_detector
cd car_detector
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/carpark_detection:0.1.0
aea install
```

Second, add the ledger info to the aea config:
``` bash
ledger_apis:
  fetchai:
    address: alpha.fetch-ai.com
    port: 80
```

Alternatively to the previous two steps, simply run:
``` bash
aea fetch fetchai/car_detector:0.1.0
cd car_detector
aea install
```

### Create carpark client agent

Then, create the carpark client agent:
``` bash
aea create car_data_buyer
cd car_data_buyer
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/carpark_client:0.1.0
aea install
```

Second, add the ledger info to the aea config:
``` bash
ledger_apis:
  fetchai:
    address: alpha.fetch-ai.com
    port: 80
```

Alternatively to the previous two steps, simply run:
``` bash
aea fetch fetchai/car_data_buyer:0.1.0
cd car_data_buyer
aea install
```

### Generate wealth for the client agent

Add a private key to the carpark client agent:
``` bash
aea generate-key fetchai
aea add-key fetchai fet_private_key.txt
```

And, fund the carpark client agent:
``` bash
cd ..
python scripts/fetchai_wealth_generation.py --private-key car_data_buyer/fet_private_key.txt --amount 10000000000 --addr alpha.fetch-ai.com --port 80
```

### Update skill configurations

Then, in the detection agent we disable the detection logic:
``` bash
aea config set skills.carpark_detection.shared_classes.strategy.args.db_is_rel_to_cwd False
```

### Run both agents

Finally, run both agents from their respective directories:
``` bash
aea run --connections oef
```

You can see that the agents find each other, negotiate and eventually trade.

### Cleaning up

When you're finished, delete your agents:
``` bash
cd ..
aea delete car_detector
aea delete car_data_buyer
```

## Communication
This diagram shows the communication between the various entities as data is successfully sold by the car park agent to the client. 

<div class="mermaid">
    sequenceDiagram
        participant Search
        participant Client_AEA
        participant Car_Park_AEA
        participant Blockchain
    
        activate Client_AEA
        activate Search
        activate Car_Park_AEA
        activate Blockchain
        
        Car_Park_AEA->>Search: register_service
        Client_AEA->>Search: search
        Search-->>Client_AEA: list_of_agents
        Client_AEA->>Car_Park_AEA: call_for_proposal
        Car_Park_AEA->>Client_AEA: propose
        Client_AEA->>Car_Park_AEA: accept
        Car_Park_AEA->>Client_AEA: match_accept
        Client_AEA->>Blockchain: transfer_funds
        Client_AEA->>Car_Park_AEA: send_transaction_hash
        Car_Park_AEA->>Client_AEA: send_data
        
        deactivate Client_AEA
        deactivate Search
        deactivate Car_Park_AEA
        deactivate Blockchain
</div>

<br />




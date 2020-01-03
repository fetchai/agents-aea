# Car Park Agent Application

The Fetch.ai car park agent demo is documented in its own repo [here](https://github.com/fetchai/carpark_agent).


## To test the AEA functionality (without the detection)


First, create the carpark detection agent:
``` bash
aea create car_detector
cd car_detector
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/carpark_detection:0.1.0
aea install
```

Then, create the carpark client agent:
``` bash
aea create car_data_buyer
cd car_data_buyer
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/carpark_client:0.1.0
aea install
aea generate-key fetchai
aea add-key fetchai fet_private_key.txt
```

Add the ledger info to both aea configs:
``` bash
ledger_apis:
  fetchai:
    address: alpha.fetch-ai.com
    port: 80
```

Fund the carpark client agent:
``` bash
cd ..
python scripts/fetchai_wealth_generation.py --private-key car_data_buyer/fet_private_key.txt --amount 10000000000 --addr alpha.fetch-ai.com --port 80
```

Then, in the detection agent we disable the detection logic:
``` bash
aea config set skills.carpark_detection.shared_classes.strategy.args.db_is_rel_to_cwd false
```

Then, launch an OEF node instance:
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

Finally, run both agents from their respective directories:
``` bash
aea run --connections oef
```

You can see that the agents find each other, negotiate and eventually trade.

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




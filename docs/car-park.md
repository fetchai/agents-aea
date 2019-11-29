# Car Park Agent Application

The Fetch.ai car park agent demo is documented in its own repo [here](https://github.com/fetchai/carpark_agent).


## To test the AEA functionality (without the detection)


First, create the carpark detection agent:
```
aea create car_detector
cd car_detector
aea add skill carpark_detection
aea install
```

Then, create the carpark client agent:
```
aea create car_data_buyer
cd car_data_buyer
aea add skill carpark_client
aea install
aea generate-key fetchai
```

Add the ledger info to both aea configs:
```
ledger_apis:
  - ledger_api:
      ledger: fetchai
      addr: alpha.fetch-ai.com
      port: 80
```

Fund the carpark client agent:
```
cd ..
python scripts/fetchai_wealth_generation.py --private-key car_data_buyer/fet_private_key.txt --amount 10000000000 --addr alpha.fetch-ai.com --port 80
```

Then, in the carpark detection agent comment out database related settings:
```
# db_is_rel_to_cwd: true
# db_rel_dir: ../temp_files
```

Then, in the client agent do:
```
max_detection_age: 36000000
```

Then, launch an OEF node instance:
```
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

Finally, run both agents with `aea run`.

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
        Blockchain->>Car_Park_AEA: transfer_complete
        Car_Park_AEA->>Client_AEA: send_data
        
        deactivate Client_AEA
        deactivate Search
        deactivate Car_Park_AEA
        deactivate Blockchain
        
    
</div>


<br />




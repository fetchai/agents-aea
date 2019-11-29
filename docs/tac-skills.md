The AEA TAC - trading agent competition - skills demonstrate an interaction between multiple AEAs in a game.

There are two types of agents:

* The tac controller which coordinates the game.
* The participant agents which compete in the game.

### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.


## Launch an OEF node
In a separate terminal, launch a local OEF node (for search and discovery).
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

Keep it running for all the following demos.

## Demo 1: no ledger transactions


### Create the TAC controller AEA
In the root directory, create the tac controller AEA.
``` bash
aea create tac_controller
```

### Add the tac control skill
``` bash
cd tac_controller
aea add skill tac_control
```

### Update the game parameters
You can change the game parameters in `tac_controller/skills/tac_control/skill.yaml` under `Parameters`.

You must set the start time to a point in the future `start_time: Nov 10 2019  10:40AM`.

### Run the TAC controller AEA
``` bash
aea run
```

### Create the TAC participants AEA
In a separate terminal, in the root directory, create the tac participant AEA.
``` bash
aea create tac_participant_one
aea create tac_participant_two
```

### Add the tac participation skill to participant one
``` bash
cd tac_participant_one
aea add skill tac_participation
aea add skill tac_negotiation
```

### Add the tac participation skill to participant two
``` bash
cd tac_participant_two
aea add skill tac_participation
aea add skill tac_negotiation
```

### Run both the TAC participant AEAs
``` bash
aea run
```

!!!	Note
	Currently, the agents cannot settle their trades. Updates coming soon!
	
### Registration communication
This diagram shows the communication between the various entities during the registration phase. 

<div class="mermaid">
    sequenceDiagram
        participant Agent_2
        participant Agent_1
        participant Search
        participant Controller
    
        activate Search
        activate Controller
        
        Controller->>Search: register_service
        activate Agent_1
        Agent_1->>Search: search
        Search-->>Agent_1: controller
        Agent_1->>Controller: register
        activate Agent_2
        Agent_2->>Search: search
        Search-->>Agent_2: controller
        Agent_2->>Controller: register
        Controller->>Agent_1: game_data
        Controller->>Agent_2: game_data
        
        deactivate Agent_1
        deactivate Agent_2
        deactivate Search
        deactivate Controller
</div>

### Transaction communication
This diagram shows the communication between the two agents and the controller. In this case, we have a Seller_Agent which is set up as a seller (and registers itself as such with the controller during the registration phase). We also have the Searching_Agent which is set up to search for sellers. 

<div class="mermaid">
    sequenceDiagram
        participant Searching_Agent
        participant Seller_Agent
        participant Controller
    
        activate Searching_Agent
        activate Seller_Agent
        activate Controller
        
        Searching_Agent->>Controller: search
        Controller-->>Searching_Agent: list_of_agents
        Searching_Agent->>Seller_Agent: call_for_proposal
        Seller_Agent->>Searching_Agent: proposal
        Searching_Agent->>Seller_Agent: accept
        Searching_Agent->>Controller: request_transaction
        Seller_Agent->>Searching_Agent: match_accept
        Seller_Agent->>Controller: request_transaction
        Controller->>Controller: transfer_funds
        
        deactivate Searching_Agent
        deactivate Seller_Agent
        deactivate Controller

</div>

In the above case, the proposal received contains a set of good which the seller wishes to sell and a cost of them. The Searching Agent needs to determine if this is a good deal for them and if so, it accepts.

There is an equivilent diagram for agents set up to search for buyers and their interaction with agents which are registered as buyers. In that scenario, the proposal will instead, be a list of goods that the buyer wishes to buy and the price it is willing to pay for them.   


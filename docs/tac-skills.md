The AEA TAC - trading agent competition - skills demonstrate an interaction between multiple AEAs in a game.

There are two types of AEAs:

* The `tac_controller` which coordinates the game.
* The `tac_participant` AEAs which compete in the game. The `tac_participant` AEAs trade tokens with each other to maximize their utility.

## Discussion

The scope of this specific demo is to demonstrate how the agents negotiate autonomously with each other while they pursue their goals by playing a game of TAC. Another AEA has the role of the controller and it's responsible for calculating the revenue for each participant and if the transaction messages are valid. Transactions are settled with the controller agent rather than against a public ledger.

## Communication

There are two types of interactions:
- between the participants and the controller, the game communication
- between the participants, the negotiation

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
        Controller->>Controller: start_game
        Controller->>Agent_1: game_data
        Controller->>Agent_2: game_data
        
        deactivate Agent_1
        deactivate Agent_2
        deactivate Search
        deactivate Controller
</div>

### Transaction communication

This diagram shows the communication between two AEAs and the controller. In this case, we have an AEA in the role of the seller, referred to as `Seller_Agent`. We also have an AEA in the role of the buyer, referred to as `Buyer_Agent`. During a given TAC, an AEA can be in both roles simultaneously in different bilateral interactions.

<div class="mermaid">
    sequenceDiagram
        participant Buyer_Agent
        participant Seller_Agent
        participant Search
        participant Controller
    
        activate Buyer_Agent
        activate Seller_Agent
        activate Search
        activate Controller
        
        Seller_Agent->>Search: register_service
        Buyer_Agent->>Search: search
        Search-->>Buyer_Agent: list_of_agents
        Buyer_Agent->>Seller_Agent: call_for_proposal
        Seller_Agent->>Buyer_Agent: proposal
        Buyer_Agent->>Seller_Agent: accept
        Seller_Agent->>Buyer_Agent: match_accept
        Seller_Agent->>Controller: transaction
        Controller->>Controller: transaction_execution
        Controller->>Seller_Agent: confirm_transaction
        Controller->>Buyer_Agent: confirm_transaction
        
        deactivate Buyer_Agent
        deactivate Seller_Agent
        deactivate Search
        deactivate Controller

</div>

In the above case, the proposal received contains a set of good which the seller wishes to sell and a cost of them. The buyer AEA needs to determine if this is a good deal for them and if so, it accepts.

There is an equivalent diagram for seller AEAs set up to search for buyers and their interaction with AEAs which are registered as buyers. In that scenario, the proposal will instead, be a list of goods that the buyer wishes to buy and the price it is willing to pay for them.   

## Option 1: AEA Manager approach

Follow this approach when using the AEA Manager Desktop app. Otherwise, skip and follow the CLI approach below. 

### Preparation instructions

Install the <a href="https://aea-manager.fetch.ai" target="_blank">AEA Manager</a>.

### Demo instructions

The following steps assume you have launched the AEA Manager Desktop app.

1. Add a new AEA called `controller` with public id `fetchai/tac_controller:0.26.0`.

2. Add another new AEA called `participant_1` with public id `fetchai/tac_participant:0.28.0`.

3. Add another new AEA called `participant_2` with public id `fetchai/tac_participant:0.28.0`.

4. Navigate to the settings of `controller` and under `components > skill >` `fetchai/fetchai/tac_controller:0.22.0` `> models > parameters > args` update `registration_start_time` to the time you want TAC to begin (e.g. 2 minutes in the future)

5. Run the `controller` AEA. Navigate to its logs and copy the multiaddress displayed. Stop the `controller`.

5. Navigate to the settings of `participant_1` and under `components > connection >` `fetchai/p2p_libp2p:0.22.0` update as follows (make sure to replace the placeholder with the multiaddress):
``` bash
{
  "delegate_uri": "127.0.0.1:11001",
  "entry_peers": ["REPLACE_WITH_MULTI_ADDRESS_HERE"],
  "local_uri": "127.0.0.1:9001",
  "log_file": "libp2p_node.log",
  "public_uri": "127.0.0.1:9001"
}
```

6. Navigate to the settings of `participant_2` and under `components > connection >` `fetchai/p2p_libp2p:0.22.0` update as follows (make sure to replace the placeholder with the multiaddress):
``` bash
{
  "delegate_uri": "127.0.0.1:11002",
  "entry_peers": ["REPLACE_WITH_MULTI_ADDRESS_HERE"],
  "local_uri": "127.0.0.1:9002",
  "log_file": "libp2p_node.log",
  "public_uri": "127.0.0.1:9002"
}
```

7. You may add more participants by repeating steps 3 (with an updated name) and 6 (bumping the port numbers. See the difference between steps 5 and 6). 

8. Run the `controller`, then `participant_1` and `participant_2` (and any other participants you added).

In the `controller`'s log, you should see the details of the transactions participants submit as well as changes in their scores and holdings. In participants' logs, you should see the agents trading.
<br>

## Option 2: CLI approach

Follow this approach when using the `aea` CLI.

## Preparation instructions

### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

## Demo instructions:

### Create TAC controller AEA

In the root directory, fetch the controller AEA:
``` bash
aea fetch fetchai/tac_controller:0.29.0
cd tac_controller
aea install
aea build
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create the controller from scratch:
``` bash
aea create tac_controller
cd tac_controller
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/ledger:0.19.0
aea add skill fetchai/tac_control:0.24.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<2.0.0,>=1.0.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.25.0
aea config set agent.default_ledger fetchai
aea config set --type dict agent.default_routing \
'{
  "fetchai/oef_search:1.0.0": "fetchai/soef:0.26.0"
}'
aea install
aea build
```

</p>
</details>

### Create the TAC participant AEAs

In a separate terminal, in the root directory, fetch at least two participants:
``` bash
aea fetch fetchai/tac_participant:0.31.0 --alias tac_participant_one
cd tac_participant_one
aea install
aea build
cd ..
aea fetch fetchai/tac_participant:0.31.0 --alias tac_participant_two
cd tac_participant_two
aea build
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

In a separate terminal, in the root directory, create at least two tac participant AEAs:
``` bash
aea create tac_participant_one
aea create tac_participant_two
```

Build participant one:
``` bash
cd tac_participant_one
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/ledger:0.19.0
aea add skill fetchai/tac_participation:0.24.0
aea add skill fetchai/tac_negotiation:0.28.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<2.0.0,>=1.0.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.25.0
aea config set agent.default_ledger fetchai
aea config set --type dict agent.default_routing \
'{
  "fetchai/ledger_api:1.0.0": "fetchai/ledger:0.19.0",
  "fetchai/oef_search:1.0.0": "fetchai/soef:0.26.0"
}'
aea config set --type dict agent.decision_maker_handler \
'{
  "dotted_path": "aea.decision_maker.gop:DecisionMakerHandler",
  "file_path": null
}'
aea install
aea build
```

Then, build participant two:
``` bash
cd tac_participant_two
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/ledger:0.19.0
aea add skill fetchai/tac_participation:0.24.0
aea add skill fetchai/tac_negotiation:0.28.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<2.0.0,>=1.0.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.25.0
aea config set agent.default_ledger fetchai
aea config set --type dict agent.default_routing \
'{
  "fetchai/ledger_api:1.0.0": "fetchai/ledger:0.19.0",
  "fetchai/oef_search:1.0.0": "fetchai/soef:0.26.0"
}'
aea config set --type dict agent.decision_maker_handler \
'{
  "dotted_path": "aea.decision_maker.gop:DecisionMakerHandler",
  "file_path": null
}'
aea install
aea build
```

</p>
</details>

### Add keys for all AEAs

Create the private key for the AEA for Fetch.ai `StargateWorld`:
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

### Update the game parameters in the controller

Navigate to the tac controller project, then use the command line to get and set the start time (set it to at least two minutes in the future):

``` bash
aea config get vendor.fetchai.skills.tac_control.models.parameters.args.registration_start_time
aea config set vendor.fetchai.skills.tac_control.models.parameters.args.registration_start_time '01 01 2020  00:01'
```

To set the registration time, you may find handy the following command:
``` bash
aea config set vendor.fetchai.skills.tac_control.models.parameters.args.registration_start_time "$(date -d "2 minutes" +'%d %m %Y %H:%M')"
```

### Update the connection parameters

Briefly run the controller AEA:

``` bash
aea run
```

Once you see a message of the form `To join its network use multiaddr 'SOME_ADDRESS'` take note of the address. (Alternatively, use `aea get-multiaddress fetchai -c -i fetchai/p2p_libp2p:0.25.0 -u public_uri` to retrieve the address.)

Then, in the participant one, run this command (replace `SOME_ADDRESS` with the correct value as described above):
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

Do the same in participant two (beware of the different port numbers):
``` bash
aea config set --type dict vendor.fetchai.connections.p2p_libp2p.config \
'{
  "delegate_uri": "127.0.0.1:11002",
  "entry_peers": ["SOME_ADDRESS"],
  "local_uri": "127.0.0.1:9002",
  "log_file": "libp2p_node.log",
  "public_uri": "127.0.0.1:9002"
}'
```

This allows the TAC participants to connect to the same local agent communication network as the TAC controller.


### Run the AEAs

First, launch the `tac_controller`:
``` bash
aea run
```

The CLI tool supports the launch of several agents
at once.

For example, assuming you followed the tutorial, you
can launch both the TAC agents as follows from the root directory:
``` bash
aea launch tac_participant_one tac_participant_two
```

You may want to try `--multithreaded`
option in order to run the agents
in the same process.

### Cleaning up

When you're finished, delete your AEAs:
``` bash
aea delete tac_controller
aea delete tac_participant_one
aea delete tac_participant_two
```
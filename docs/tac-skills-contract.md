The AEA TAC - trading agent competition - skills demonstrate an interaction between multiple AEAs in a game.

There are two types of AEAs:

* The `tac_controller` which coordinates the game.
* The `tac_participant` AEAs which compete in the game. The `tac_participant` AEAs trade tokens with each other to maximize their utility.

## Discussion

The scope of the specific demo is to demonstrate how the agents negotiate autonomously with each other while they pursue their goals by playing a game of TAC. This demo uses another AEA - a controller AEA - to take the role of running the competition. Transactions are validated on an ERC1155 smart contract on the Ropsten Ethereum testnet.

In the below video we discuss the framework and TAC in more detail:

<iframe width="560" height="315" src="https://www.youtube.com/embed/gvzYX7CYk-A" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

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
        Controller->>Agent_1: game_data
        Controller->>Agent_2: game_data
        
        deactivate Agent_1
        deactivate Agent_2
        deactivate Search
        deactivate Controller
</div>

### Transaction communication
This diagram shows the communication between the two AEAs and the controller. In this case, we have a `Seller_Agent` which is set up as a seller (and registers itself as such with the controller during the registration phase). We also have the `Searching_Agent` which is set up to search for sellers. 

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


## Preparation instructions

### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

## Demo instructions:

### Create TAC controller AEA

In the root directory, fetch the controller AEA:
``` bash
aea fetch fetchai/tac_controller_contract:0.23.0
cd tac_controller_contract
aea install
aea build
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create the controller from scratch:
``` bash
aea create tac_controller_contract
cd tac_controller_contract
aea add connection fetchai/p2p_libp2p:0.17.0
aea add connection fetchai/soef:0.18.0
aea add connection fetchai/ledger:0.14.0
aea add skill fetchai/tac_control_contract:0.19.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<0.2.0,>=0.1.0"},
  "aea-ledger-ethereum": {"version": "<0.2.0,>=0.1.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.17.0
aea config set agent.default_ledger ethereum
aea config set vendor.fetchai.connections.soef.config.chain_identifier ethereum
aea config set --type bool vendor.fetchai.skills.tac_control.is_abstract true
aea config set --type dict agent.default_routing \
'{
  "fetchai/contract_api:0.12.0": "fetchai/ledger:0.14.0",
  "fetchai/ledger_api:0.11.0": "fetchai/ledger:0.14.0",
  "fetchai/oef_search:0.14.0": "fetchai/soef:0.18.0"
}'
aea config set --type list vendor.fetchai.connections.p2p_libp2p.cert_requests \
'[{"identifier": "acn", "ledger_id": "ethereum", "not_after": "2022-01-01", "not_before": "2021-01-01", "public_key": "fetchai", "save_path": ".certs/conn_cert.txt"}]'
aea install
aea build
```

</p>
</details>

Then, generate a private key.
``` bash
aea generate-key ethereum
aea add-key ethereum ethereum_private_key.txt
```

### Create the TAC participant AEAs

In a separate terminal, in the root directory, fetch at least two participants:
``` bash
aea fetch fetchai/tac_participant:0.23.0 --alias tac_participant_one
cd tac_participant_one
aea generate-key ethereum
aea add-key ethereum ethereum_private_key.txt
aea install
aea build
cd ..
aea fetch fetchai/tac_participant:0.23.0 --alias tac_participant_two
cd tac_participant_two
aea generate-key ethereum
aea add-key ethereum ethereum_private_key.txt
aea install
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
aea add connection fetchai/p2p_libp2p:0.17.0
aea add connection fetchai/soef:0.18.0
aea add connection fetchai/ledger:0.14.0
aea add skill fetchai/tac_participation:0.18.0
aea add skill fetchai/tac_negotiation:0.21.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<0.2.0,>=0.1.0"},
  "aea-ledger-ethereum": {"version": "<0.2.0,>=0.1.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.17.0
aea config set agent.default_ledger ethereum
aea config set vendor.fetchai.connections.soef.config.chain_identifier ethereum
aea config set vendor.fetchai.skills.tac_participation.models.game.args.is_using_contract 'True' --type bool
aea config set vendor.fetchai.skills.tac_negotiation.models.strategy.args.is_contract_tx 'True' --type bool
aea config set --type dict agent.default_routing \
'{
  "fetchai/contract_api:0.12.0": "fetchai/ledger:0.14.0",
  "fetchai/ledger_api:0.11.0": "fetchai/ledger:0.14.0",
  "fetchai/oef_search:0.14.0": "fetchai/soef:0.18.0"
}'
aea config set --type dict agent.decision_maker_handler \
'{
  "dotted_path": "aea.decision_maker.gop:DecisionMakerHandler",
  "file_path": null
}'
aea config set --type list vendor.fetchai.connections.p2p_libp2p.cert_requests \
'[{"identifier": "acn", "ledger_id": "ethereum", "not_after": "2022-01-01", "not_before": "2021-01-01", "public_key": "fetchai", "save_path": ".certs/conn_cert.txt"}]'
aea generate-key ethereum
aea add-key ethereum ethereum_private_key.txt
aea install
aea build
```

Then, build participant two:
``` bash
cd tac_participant_two
aea add connection fetchai/p2p_libp2p:0.17.0
aea add connection fetchai/soef:0.18.0
aea add connection fetchai/ledger:0.14.0
aea add skill fetchai/tac_participation:0.18.0
aea add skill fetchai/tac_negotiation:0.21.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<0.2.0,>=0.1.0"},
  "aea-ledger-ethereum": {"version": "<0.2.0,>=0.1.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.17.0
aea config set agent.default_ledger ethereum
aea config set vendor.fetchai.connections.soef.config.chain_identifier ethereum
aea config set vendor.fetchai.skills.tac_participation.models.game.args.is_using_contract 'True' --type bool
aea config set vendor.fetchai.skills.tac_negotiation.models.strategy.args.is_contract_tx 'True' --type bool
aea config set --type dict agent.default_routing \
'{
  "fetchai/contract_api:0.12.0": "fetchai/ledger:0.14.0",
  "fetchai/ledger_api:0.11.0": "fetchai/ledger:0.14.0",
  "fetchai/oef_search:0.14.0": "fetchai/soef:0.18.0"
}'
aea config set --type dict agent.decision_maker_handler \
'{
  "dotted_path": "aea.decision_maker.gop:DecisionMakerHandler",
  "file_path": null
}'
aea config set --type list vendor.fetchai.connections.p2p_libp2p.cert_requests \
'[{"identifier": "acn", "ledger_id": "ethereum", "not_after": "2022-01-01", "not_before": "2021-01-01", "public_key": "fetchai", "save_path": ".certs/conn_cert.txt"}]'
aea generate-key ethereum
aea add-key ethereum ethereum_private_key.txt
aea install
aea build
```

</p>
</details>

### Add keys for all AEAs

Create a private key used to secure the AEA's communications:
``` bash
aea generate-key fetchai fetchai_connection_private_key.txt
aea add-key fetchai fetchai_connection_private_key.txt --connection
```

Finally, certify the key for use by the connections that request that:
``` bash
aea issue-certificates
```

### Update the game parameters in the controller

Navigate to the tac controller project, then use the command line to get and set the start time (set it to at least five minutes - better 10 - in the future):

``` bash
aea config get vendor.fetchai.skills.tac_control_contract.models.parameters.args.registration_start_time
aea config set vendor.fetchai.skills.tac_control_contract.models.parameters.args.registration_start_time '01 01 2020  00:01'
```

To set the registration time, you may find handy the following command:
``` bash
aea config set vendor.fetchai.skills.tac_control_contract.models.parameters.args.registration_start_time "$(date -d "2 minutes" +'%d %m %Y %H:%M')"
```


### Update the connection parameters

Briefly run the controller AEA:

``` bash
aea run
```

Once you see a message of the form `To join its network use multiaddr 'SOME_ADDRESS'` take note of the address. (Alternatively, use `aea get-multiaddress fetchai -c -i fetchai/p2p_libp2p:0.17.0 -u public_uri` to retrieve the address.)


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


## Run Ganache

Run the following command
``` bash
docker run -p 8545:8545 trufflesuite/ganache-cli:latest --verbose --gasPrice=0 --gasLimit=0x1fffffffffffff --account="$(cat tac_controller_contract/ethereum_private_key.txt),1000000000000000000000" --account="$(cat tac_participant_one/ethereum_private_key.txt),1000000000000000000000" --account="$(cat tac_participant_two/ethereum_private_key.txt),1000000000000000000000"
```

To check the wealth of one of the AEAs, use:

``` bash
aea get-wealth ethereum
```

You should get `1000000000000000000000`.

### Run the AEAs

First, launch the `tac_contract_controller`:
``` bash
aea run tac_contract_controller
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
aea delete tac_controller_contract
aea delete tac_participant_one
aea delete tac_participant_two
```
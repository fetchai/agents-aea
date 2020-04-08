The AEA TAC - trading agent competition - skills demonstrate an interaction between multiple AEAs in a game.

There are two types of AEAs:

* The `tac_controller` which coordinates the game.
* The `tac_participant` AEAs which compete in the game. The `tac_participant` AEAs trade tokens with each other to maximize their utility.

### Discussion

The scope of the specific demo is to demonstrate how the agents negotiate autonomously with each other while they pursue their goals by playing a game of TAC.
An other AEA has the role of the controller and it's responsible for calculating the revenue for each participant and if the transaction messages are valid.

## Preparation instructions

### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

### Launch an OEF search and communication node
In a separate terminal, launch a local [OEF search and communication node](../oef-ledger).
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

Keep it running for all the following demos.

## Demo instructions 1: no ledger transactions

This demo uses another AEA - a controller AEA - to take the role of running the competition and validating the transactions negotiated by the AEAs. 

### Create the TAC controller AEA
In the root directory, create the tac controller AEA and enter the project.
``` bash
aea create tac_controller
cd tac_controller
```

### Add the tac control skill
``` bash
aea add connection fetchai/oef:0.2.0
aea add skill fetchai/tac_control:0.1.0
aea add contract fetchai/erc1155:0.1.0
aea install
aea config set agent.default_connection fetchai/oef:0.2.0
```

Add the following configs to the aea config:
``` yaml
ledger_apis:
  ethereum:
    address: https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe
    chain_id: 3
    gas_price: 20
```

Set the default ledger to ethereum:
``` bash
aea config set agent.default_ledger ethereum
```

### Update the game parameters
You can change the game parameters in `tac_controller/skills/tac_control/skill.yaml` under `Parameters`.

You must set the start time to a point in the future `start_time: 12 11 2019  15:01`.

Alternatively, use the command line to get and set the start time:

``` bash
aea config get vendor.fetchai.skills.tac_control.models.parameters.args.start_time
aea config set vendor.fetchai.skills.tac_control.models.parameters.args.start_time '01 01 2020  00:01'
```

### Run the TAC controller AEA
``` bash
aea run --connections fetchai/oef:0.2.0
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
aea add connection fetchai/oef:0.2.0
aea add skill fetchai/tac_participation:0.1.0
aea add skill fetchai/tac_negotiation:0.1.0
aea add contract fetchai/erc1155:0.1.0
aea install
aea config set agent.default_connection fetchai/oef:0.2.0
```

Set the default ledger to ethereum:
``` bash
aea config set agent.default_ledger ethereum
```

### Add the tac participation skill to participant two
``` bash
cd tac_participant_two
aea add connection fetchai/oef:0.2.0
aea add skill fetchai/tac_participation:0.1.0
aea add skill fetchai/tac_negotiation:0.1.0
aea add contract fetchai/erc1155:0.1.0
aea install
aea config set agent.default_connection fetchai/oef:0.2.0
```

Set the default ledger to ethereum:
``` bash
aea config set agent.default_ledger ethereum
```

### Run both the TAC participant AEAs
``` bash
aea run --connections fetchai/oef:0.2.0
```
	
## Using `aea fetch` and `aea launch`

You can fetch the finished agents:
``` bash
aea fetch fetchai/tac_controller:0.1.0
aea fetch fetchai/tac_participant:0.1.0
```

The CLI tool supports the launch of several agents
at once.

For example, assuming you followed the tutorial, you
can launch the TAC agents as follows:

- set the default connection `fetchai/oef:0.2.0` for every
agent;
- run:
```bash
aea launch tac_controller tac_participant_one tac_participant_two
```

	
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
This diagram shows the communication between the two AEAs and the controller. In this case, we have a Seller_Agent which is set up as a seller (and registers itself as such with the controller during the registration phase). We also have the Searching_Agent which is set up to search for sellers. 

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


## Negotiation skill - deep dive

The AEA `tac_negotiation` skill demonstrates how negotiation strategies may be embedded into an Autonomous Economic Agent.

The `tac_negotiation` skill `skill.yaml` configuration file looks like this.

``` yaml
name: tac_negotiation
authors: fetchai
version: 0.1.0
license: Apache-2.0
description: "The tac negotiation skill implements the logic for an AEA to do fipa negotiation in the TAC."
behaviours:
  behaviour:
      class_name: GoodsRegisterAndSearchBehaviour
      args:
        services_interval: 5
  clean_up:
    class_name: TransactionCleanUpBehaviour
    args:
      tick_interval: 5.0
handlers:
  fipa:
    class_name: FIPANegotiationHandler
    args: {}
  transaction:
    class_name: TransactionHandler
    args: {}
  oef:
    class_name: OEFSearchHandler
    args: {}
models:
  search:
    class_name: Search
    args:
      search_interval: 5
  registration:
    class_name: Registration
    args:
      update_interval: 5
  strategy:
    class_name: Strategy
    args:
      register_as: both
      search_for: both
  dialogues:
    class_name: Dialogues
    args: {}
  transactions:
    class_name: Transactions
    args:
      pending_transaction_timeout: 30
protocols: ['fetchai/oef_search:0.1.0', 'fetchai/fipa:0.1.0']
```

Above, you can see the registered `Behaviour` class name `GoodsRegisterAndSearchBehaviour` which implements register and search behaviour of an AEA for the `tac_negotiation` skill.

The `FIPANegotiationHandler` deals with receiving `FipaMessage` types containing FIPA negotiation terms, such as `cfp`, `propose`, `decline`, `accept` and `match_accept`.

The `TransactionHandler` deals with `TransactionMessage`s received from the decision maker component. The decision maker component is responsible for cryptoeconomic security.

The `OEFSearchHandler` deals with `OefSearchMessage` types returned from the [OEF search node](../oef-ledger)

The `TransactionCleanUpBehaviour` is responsible for cleaning up transactions which are no longer likely to being settled with the controller AEA.

### Models

The `models` element in the configuration `yaml` lists a number of important classes which are shared between the handlers, behaviours and tasks.

#### Search

This class abstracts the logic required by AEAs performing searches for other buying/selling AEAs according to strategy (see below).

#### Registration

This class abstracts the logic required by AEAs performing service registrations on the [OEF search node](../oef-ledger).

#### Strategy

This class defines the strategy behind an AEA's activities.

The class is instantiated with the AEA's goals, for example whether the AEA intends to buy/sell something, and is therefore looking for other sellers, buyers, or both.

It also provides methods for defining what goods AEAs are looking for and what goods they may have to sell, for generating proposal queries, and checking whether a proposal is profitable or not.

#### Dialogue

`Dialogues` abstract the negotiations that take place between AEAs including all negotiation end states, such as accepted, declined, etc. and all the negotiation states in between.

#### Transactions

This class deals with representing potential transactions between AEAs.

!!!	Note
	Work in progress.

The AEA FIPA skill demonstrates how FIPA negotiation strategies may be embedded into an Autonomous Economic Agent.

## Configuration

The FIPA skill `skill.yaml` configuration file looks like this.

``` yaml
name: ''
authors: Fetch.AI Limited
version: 0.1.0
license: Apache 2.0
url: ""
behaviours:
  - behaviour:
      class_name: GoodsRegisterAndSearchBehaviour
      args:
        services_interval: 5
handlers:
  class_name: FIPANegotiationHandler
tasks:
  - task:
      class_name: TransactionCleanUpTask
shared_classes:
  - one:
    class_name: Search
  - two:
    class_name: Strategy
  - three:
    class_name: Dialogues
  - four:
    class_name: Transactions
    args:
      pending_transaction_timeout: 30
protocol: ['oef', 'fipa']
```

Above, you can see the registered `Behaviour` class name `GoodsRegisterAndSearchBehaviour` which implements register and search behaviour of an AEA for the FIPA skill.

The `FIPANegotiationHandler` deals with receiving `FIPAMessage` types containing FIPA negotiation terms, such as `propose`, `decline`, `accept`, etc.

The `TransactionCleanUpTask` does ...tbc.

## Shared classes

The `shared_classes` element in the configuration `yaml` lists a number of important classes for agents communicating via the FIPA skill.

### Search

This class abstracts the logic required by agents performing searches for other buying/selling agents according to strategy (see below).

### Strategy

This class defines the strategy behind an agent's activities.

The class is instantiated with the agent's goals, for example whether the agent intends to buy/sell something, and is therefore looking for other sellers, buyers, or both.

It also provides methods for defining what goods agents are looking for and what goods they may have to sell, for generating proposal queries, and checking whether a proposal is profitable or not.

### Dialogue

`Dialogues` abstract the negotiations that take place between agents including all negotiation end states, such as accepted, declined, etc. and all the negotiation states in between.

### Transactions

This class deals with finalising negotiation proposals between agents.




## Demo instructions

!!!	Warn
	Fipa negotiation skill is not fully developed.


Follow the Preliminaries and Installation instructions <a href="../quickstart">here</a>.


Then, download the examples and packages directory.
``` bash
svn export https://github.com/fetchai/agents-aea.git/trunk/packages
```

### Create the agent
In the root directory, create the fipa agent.
``` bash
aea create my_fipa_agent
```


### Add the fipa skill 
``` bash
cd my_fipa_agent
aea add skill fipa_negotiation
```

### Add the local connection
``` bash
aea add connection local
```

### Run the agent with the default connection

``` bash
aea run --connection local
```

You will see the fipa logs.

<!--
<center>![FIPA logs](assets/gym-training.png)</center>
-->

### Delete the agent

When you're done, go up a level and delete the agent.

``` bash
aea delete my_fipa_agent
```


<br/>
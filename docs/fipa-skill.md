<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>Work in progress.</p>
</div>

The AEA FIPA skill demonstrates how FIPA negotiation strategies may be embedded into an Autonomous Economic Agent.

## Configuration

The FIPA skill `skill.yaml` configuration file looks like this.

```yaml
name: 'fipa_negotiation'
authors: Fetch.ai Limited
version: 0.1.0
license: Apache 2.0
url: ''
behaviours:
    - behaviour:
          class_name: GoodsRegisterAndSearchBehaviour
          args:
              services_interval: 5
handlers:
    - handler:
          class_name: FIPANegotiationHandler
          args: {}
tasks:
    - task:
          class_name: TransactionCleanUpTask
          args: {}
shared_classes:
    - shared_class:
          class_name: Search
          args: {}
    - shared_class:
          class_name: Strategy
          args: {}
    - shared_class:
          class_name: Dialogues
          args: {}
    - shared_class:
          class_name: Transactions
          args:
              pending_transaction_timeout: 30
protocols: ['oef', 'fipa']
```

Above, you can see the registered `Behaviour` class name `GoodsRegisterAndSearchBehaviour` which implements register and search behaviour of an AEA for the FIPA skill.

The `FIPANegotiationHandler` deals with receiving `FIPAMessage` types containing FIPA negotiation terms, such as `cfp`, `propose`, `decline`, `accept` and `match_accept`.

The `TransactionCleanUpTask` takes care of removing potential transaction of different degrees of commitment from the potential transactions list if they are unlikely to be settled.

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

This class deals with representing potential transactions between agents.

## Demo instructions

!!! Warn
FIPA negotiation skill is not fully developed.

Follow the Preliminaries and Installation instructions <a href="../quickstart" target=_blank>here</a>.

Then, download the examples and packages directory.

```bash
svn export https://github.com/fetchai/agents-aea.git/trunk/packages
```

### Create the agent

In the root directory, create the FIPA agent.

```bash
aea create my_fipa_agent
```

### Add the FIPA skill

```bash
cd my_fipa_agent
aea add skill fipa_negotiation
```

### Add the local connection

```bash
aea add connection local
```

### Run the agent with the default connection

```bash
aea run --connection local
```

<!--
You will see the FIPA logs.

<center>![FIPA logs](assets/gym-training.png)</center>
-->

### Delete the agent

When you're done, go up a level and delete the agent.

```bash
cd ..
aea delete my_fipa_agent
```

<br/>

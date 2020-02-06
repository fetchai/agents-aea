## Multiplexer

The `Multiplexer` is responsible for maintaining potentially multiple connections.

### Connection

Connections wrap an external SDK or API and manage messaging. As such, they allow the agent to connect to an external service with an exposed Python SDK/API.

The module `connections/base.py` contains the abstract class which defines a `Connection`. A `Connection` acts as a bridge to the SDK or API to be wrapped, and is, where necessary, responsible for translating between the framework specific `Envelope` with its contained `Message` and the external service.

The framework provides one default connection:

* `stub`: implements an I/O reader and writer to send messages to the agent from a local file.

### InBox and OutBox

The `InBox` and `OutBox` are, respectively, queues for incoming and outgoing `Envelopes`. They are needed to separate the thread which runs the `Multiplexer` from the thread which runs the main agent loop.

### Envelope

An `Envelope` is the core object with which agents communicate. It travels from `OutBox` to another agent or gets translated in the `Connection` to an external service or protocol. `Envelope` objects sent from other agents arrive in the `InBox` via a `Connection`. An `Envelope` is a vehicle for messages with five attribute parameters:

* `to`: defines the destination address.

* `sender`: defines the sender address.

* `protocol_id`: defines the id of the protocol.

* `message`: is a bytes field which holds the message in serialized form.

* `Optional[context]`: an optional field to specify routing information in a URI.


### Protocol

Protocols define how messages are represented and encoded for transport. They also define the rules to which messages have to adhere in a message sequence. 

For instance, a protocol may contain messages of type `START` and `FINISH`. From there, the rules may prescribe that a message of type `FINISH` must be preceded by a message of type `START`.

The `Message` class in the `protocols/base.py` module provides an abstract class with all the functionality a derived `Protocol` message class requires for a custom protocol, such as basic message generating and management functions and serialisation details.

The framework provides one default protocol:

* `default`: this protocol provides a bare bones implementation for an AEA protocol which includes a `DefaultMessage` class and a `DefaultSerialization` class with functions for managing serialisation. Use this protocol as a starting point for building custom protocols.


Additional protocols can be added as packages, including:

* `oef`: this protocol provides the AEA protocol implementation for communication with the OEF including an `OEFMessage` class for hooking up to OEF services and search agents. Utility classes are available in the `models.py` module which provides OEF specific requirements, such as classes, needed to perform querying on the OEF, such as `Description`, `Query`, and `Constraint`, to name a few.
* `fipa`: this protocol provides classes and functions necessary for communication between AEAs via a variant of the [FIPA](http://www.fipa.org/repository/aclspecs.html) Agent Communication Language. For example, the `FIPAMessage` class provides negotiation terms such as `cfp`, `propose`, `decline`, `accept` and `match_accept`.

### Skill

Skills are a result of the framework's extensibility. They are self-contained capabilities that AEAs can dynamically take on board, 
in order to expand their effectiveness in different situations. 
A skill can be given permission to read the internal state of the the AEA, and suggest action(s) to the AEA according to its specific logic. 
As such, more than one skill could exist per protocol, competing with each other in suggesting to the AEA the best course of actions to take. 

For instance, an AEA who is trading goods, could subscribe to more than one skill, where each skill corresponds to a different trading strategy. 
The skills could then read the internal state of the AEA, and independently suggest profitable transactions. 

A skill encapsulates implementations of the abstract base classes `Handler`, `Behaviour`, and `Task`:

* `Handler`: each skill has none, one or more `Handler` objects, each responsible for the registered messaging protocol. Handlers implement AEAs' reactive behaviour. If the AEA understands the protocol referenced in a received `Envelope`, the `Handler` reacts appropriately to the corresponding message. Each `Handler` is responsible for only one protocol. A `Handler` is also capable of dealing with internal messages.
* `Behaviour`: none, one or more `Behaviours` encapsulate actions that cause interactions with other agents initiated by the AEA. Behaviours implement AEAs' pro-activeness.
* `Task`: none, one or more `Tasks` encapsulate background work internal to the AEA.

Skills further allow for `Models`. Classes that inherit from the `Model` can be accessed via the `SkillContext`.


## Agent 

### Main loop

The `_run_main_loop()` function in the `Agent` class performs a series of activities while the `Agent` state is not stopped.

* `act()`: this function calls the `act()` function of all active registered Behaviours.
* `react()`: this function grabs all Envelopes waiting in the `InBox` queue and calls the `handle()` function for the Handlers currently registered against the protocol of the `Envelope`.
* `update()`: this function loops through all the Tasks and executes them.


## Decision maker

The `DecisionMaker` component manages global agent state updates proposed by the skills and processes the resulting ledger transactions.

It is responsible for the AEA's crypto-economic security and goal management, and it contains the preference and ownership representation of the AEA.

### TransactionMessage and StateUpdateMessage

Skills communicate with the decision maker via `InternalMessages`. There exist two types of these: `TransactionMessage` and `StateUpdateMessage`.

The `StateUpdateMessage` is used to initialize the decision maker with preferences and ownership states. It can also be used to update the ownership states in the decision maker if the settlement of transaction takes place off chain.

The `TransactionMessage` is used by a skill to propose a transaction to the decision maker. The performative `TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT` is used by a skill to propose a transaction which the decision maker is supposed to settle on chain. The performative `TransactionMessage.Performative.PROPOSE_FOR_SIGNING` is used by the skill to propose a transaction which the decision maker is supposed to sign and which will be settled later.

The decision maker processes messages and can accept or reject them.

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>For examples how to use these concepts have a look at the `tac_` skills. These functionalities are experimental and subject to change.
</p>
</div>

## Filter

`Filter` routes messages to the correct `Handler` via `Resource`. It also holds a reference to the currently active `Behaviour` and `Task` instances.

By default for every skill, each `Handler`, `Behaviour` and `Task` is registered in the `Filter`. However, note that skills can de-active and re-activate themselves.

The `Filter` also routes internal messages from the `DecisionMaker` to the respective `Handler` in the skills.

## Resource 

The `Resource` component is made up of `Registries` for each type of resource (e.g. `Protocol`, `Handler`, `Behaviour`, `Task`). 

Message Envelopes travel through the `Filter` which in turn fetches the correct `Handler` from the `Registry`.

Specific `Registry` classes are in the `registries/base.py` module.

* `ProtocolRegistry`.
* `HandlerRegistry`. 
* `BehaviourRegistry`.
* `TaskRegistry`.



<br />


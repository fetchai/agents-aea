### MailBox

A `MailBox` contains `InBox` and `OutBox` queues containing `Envelopes`.


### Envelope

An `Envelope` is the core object with which agents communicate. It is a vehicle for messages with four attribute parameters:

* `to`: defines the destination address.

* `sender`: defines the sender address.

* `protocol_id`: defines the id of the protocol.

* `message`: is a bytes field which holds the message in serialized form.


### Protocol

Protocols define how messages are represented and encoded for transport. They also define the rules to which messages have to adhere in a message sequence. 

For instance, a protocol may contain messages of type `START` and `FINISH`. From there, the rules may prescribe that a message of type `FINISH` must be preceded by a message of type `START`.

The `Message` class in the `protocols/base.py` module provides an abstract class with all the functionality a derived `Protocol` message class requires for a custom protocol, such as basic message generating and management functions and serialisation details.

A number of protocols come packaged up with the AEA framework.

* `default`: this protocol provides a bare bones implementation for an AEA protocol which includes a `DefaultMessage` class and a `DefaultSerialization` class with functions for managing serialisation. Use this protocol as a starting point for building custom protocols.
* `oef`: this protocol provides the AEA protocol implementation for communication with the OEF including an `OEFMessage` class for hooking up to OEF services and search agents. Utility classes are available in the `models.py` module which provides OEF specific requirements such as classes needed to perform querying on the OEF such as `Description`, `Query`, and `Constraint`, to name a few.
* `fipa`: this protocol provides classes and functions necessary for communication between AEAs via the [FIPA](http://www.fipa.org/repository/aclspecs.html) Agent Communication Language. For example, the `FIPAMessage` class provides negotiation terms such as `cfp`, `propose`, `decline`, `accept` and `match_accept`.


### Connection

Connections wrap an external SDK or API and manage messaging. As such, they allow the agent to connect to an external service with an exposed Python SDK/API.

The module `connections/base.py` contains two abstract classes which define a `Channel` and a `Connection`. A `Connection` contains one `Channel`, which acts as a bridge to the SDK or API to be wrapped. The `Channel` is responsible for translating between the framework specific `Envelope` with its contained `Message` and the external service.

The framework provides a number of default connections.

* `local`: implements a local node.
* `oef`: wraps the OEF SDK.

<!-- other connections? gym? -->


### Skill

<!-- Skills are the manifestation of the framework's extensibility. 
A skill is an atomic capability that suggests enables the agent perform a specific  delivers economic value by allowing the agent encapsulate and call any kind of code. A skill encapsulates implementations of the abstract base classes `Handler`, `Behaviour`, and `Task`.
--> 

<!-- From this, it is really not clear what skills do, and what their purpose is, what the idea behind them is, etc. --> 
Skills deliver economic value to the AEA by letting the agent call any kind of code. A skill encapsulates implementations of the abstract base classes `Handler`, `Behaviour`, and `Task`.

* `Handler`: each skill has none, one or more `Handler` objects, each responsible for the registered messaging protocol. Handlers implement agents' reactive behaviour. By understanding the requirements <!-- which requirements?, where in the envelope?--> contained in an `Envelope`, the `Handler` reacts appropriately to the received messages. Each `Handler` is responsible for only one protocol.
* `Behaviour`: none, one or more `Behaviours` encapsulate actions that cause interactions with other agents initiated by the agent. Behaviours implement agents' proactiveness.
* `Task`: none, one or more Tasks encapsulate background work internal to the agent.


## Agent 

### Main loop

The `_run_main_loop()` function in the `Agent` class performs a series of activities while the `Agent` state is not stopped.

* `act()`: this function calls the `act()` function of all registered Behaviours.
* `react()`: this function grabs all Envelopes waiting in the `InBox` queue and calls the `handle()` function for the Handlers currently registered against the protocol of the `Envelope`.
* `update()`: this function loops through all the Tasks and executes them.


## Decision maker

The `DecisionMaker` component manages global agent state updates proposed by the skills and processes the resulting ledger transactions.

It is responsible for the agent's crypto-economic interactions and goal management, and it contains the preference and ownership representation of the agent.


## Filter

`Filter` routes messages to the correct `Handler` via `Resource`. It also holds a reference to the currently active `Behaviour` and `Task` instances.

By default for every skill, each `Handler`, `Behaviour` and `Task` is registered in the `Filter`. However, note that skills can de-register and re-register themselves.

## Resource 

The `Resource` component is made up of `Registries` for each type of resource (e.g. `Protocol`, `Handler`, `Behaviour`, `Task`). 

Message Envelopes travel through the `Filter` which in turn fetches the correct `Handler` from the `Registry`.

Specific `Registry` classes are in the `registries/base.py` module.

* `ProtocolRegistry`.
* `HandlerRegistry`. 
* `BehaviourRegistry`.
* `TaskRegistry`.



<br />


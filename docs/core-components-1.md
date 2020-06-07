The AEA framework consists of several core elements, some which are required to run an AEA and others which are optional.

## The elements each AEA uses

<a href="api/aea">AEAs</a> communicate asynchronously via envelopes.

### Envelope

An <a href="api/mail/base">Envelope</a> is the core object with which agents communicate. An `Envelope` is a vehicle for messages with five attribute parameters:

* `to`: defines the destination address.

* `sender`: defines the sender address.

* `protocol_id`: defines the id of the protocol.

* `message`: is a bytes field which holds the message in serialized form.

* `Optional[context]`: an optional field to specify routing information in a URI.

Messages must adhere to a protocol.

### Protocol

Protocols define how messages are represented and encoded for transport. They also, optionally, define the rules to which messages have to adhere in a message sequence. 

For instance, a protocol may contain messages of type `START` and `FINISH`. From there, the rules may prescribe that a message of type `FINISH` must be preceded by a message of type `START`.

The <a href="api/protocols/base">Message</a> class in the `protocols/base.py` module provides an abstract class with all the functionality a derived `Protocol` message class requires for a custom protocol, such as basic message generating and management functions and serialisation details.

The framework provides one default protocol, called `default`. This protocol provides a bare bones implementation for an AEA protocol which includes a `DefaultMessage` class and a `DefaultSerialization` class with functions for managing serialisation.

Additional protocols can be added as packages or generated with the <a href="protocol-generator">protocol generator</a>.

Protocol specific messages, wrapped in envelopes, are sent and received to other agents and services via connections.

### Connection

The module `connections/base.py` contains the abstract class which defines a <a href="api/connections/base">Connection</a>. A `Connection` acts as a bridge to the SDK or API to be wrapped, and is, where necessary, responsible for translating between the framework specific `Envelope` with its contained `Message` and the external service or third-party protocol (e.g. `HTTP`).

The framework provides one default connection, called `stub`. It implements an I/O reader and writer to send messages to the agent from a local file. Additional connections can be added as packages.

An AEA can run connections via the `Multiplexer`.

### Multiplexer

The <a href="api/mail/base">Multiplexer</a> is responsible for maintaining potentially multiple connections.

It maintains an `InBox` and `OutBox`, which are, respectively, queues for incoming and outgoing `Envelopes`. They are used to separate the main agent loop from the loop which runs the `Multiplexer`.

### Skill

<a href="api/skill/base">Skills</a> are the core focus of the framework's extensibility. They are self-contained capabilities that AEAs can dynamically take on board, in order to expand their effectiveness in different situations.

A skill encapsulates implementations of the three abstract base classes `Handler`, `Behaviour`, `Model`, and is closely related with the abstract base class `Task`:

* `Handler`: each skill has none, one or more `Handler` objects, each responsible for the registered messaging protocol. Handlers implement AEAs' reactive behaviour. If the AEA understands the protocol referenced in a received `Envelope`, the `Handler` reacts appropriately to the corresponding message. Each `Handler` is responsible for only one protocol. A `Handler` is also capable of dealing with internal messages (see next section).
* `Behaviour`: none, one or more `Behaviours` encapsulate actions that cause interactions with other agents initiated by the AEA. Behaviours implement AEAs' pro-activeness.
* `Models`: none, one or more `Models` that inherit from the `Model` can be accessed via the `SkillContext`.
* `Task`: none, one or more `Tasks` encapsulate background work internal to the AEA.

`Task` differs from the other three in that it is not a part of skills, but `Task`s are declared in or from skills if a packaging approach for AEA creation is used.

A skill can read (parts of) the state of the the AEA, and suggest action(s) to the AEA according to its specific logic.  As such, more than one skill could exist per protocol, competing with each other in suggesting to the AEA the best course of actions to take. 

For instance, an AEA who is trading goods, could subscribe to more than one skill, where each skill corresponds to a different trading strategy.  The skills could then read the preference and ownership state of the AEA, and independently suggest profitable transactions.

The framework provides one default skill, called `error`. Additional skills can be added as packages.

### Main loop

The main agent loop performs a series of activities while the `Agent` state is not stopped.

* `act()`: this function calls the `act()` function of all active registered Behaviours (described below).
* `react()`: this function grabs all Envelopes waiting in the `InBox` queue and calls the `handle()` function for the Handlers currently registered against the protocol of the `Envelope`.
* `update()`: this function dispatches the internal messages from the decision maker (described below) to the handler in the relevant skill.

## Next steps

### Recommended

We recommend you continue with the next step in the 'Getting Started' series:

- <a href="../aea-vs-mvc/">AEA and web frameworks</a>

### Relevant deep-dives

Most AEA development focuses on developing the skills and protocols necessary for an AEA to deliver against its economic objectives.

Understanding protocols is core to developing your own agent. You can learn more about the protocols agents use to communicate with each other and how they are created in the following section:

- <a href="../protocol/">Protocols</a>

Most of an AEA developer's time is spent on skill development. Skills are the core business logic commponents of an AEA. Check out the following guide to learn more:

- <a href="../skill/">Skills</a>

In most cases, one of the available connection packages can be used. Occassionally, you might develop your own connection:

- <a href="../connection/">Connections</a>

<br />


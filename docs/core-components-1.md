The AEA framework consists of several core elements, some which are required to run an AEA and others which are optional.

## The elements each AEA uses

<a href="../api/aea#aea-objects">`AEAs`</a> communicate asynchronously via envelopes.

### Envelope

<img src="/assets/envelope.png" alt="Envelope of an AEA" class="center" style="display: block; margin-left: auto; margin-right: auto;width:50%;">

An <a href="../api/mail/base#envelope-objects">`Envelope`</a> is the core object with which agents communicate. It is a vehicle for messages with five attribute parameters:

* `to`: defines the destination address.

* `sender`: defines the sender address.

* `protocol_id`: defines the id of the protocol.

* `message`: is a bytes field which holds the message in serialized form.

* `Optional[context]`: an optional field to specify routing information in a URI.

Messages must adhere to a protocol.

### Protocol

<a href="../api/protocols/base#protocol-objects">`Protocols`</a> define agent to agent interactions, which include:

* messages, which define the representation;

* serialization logic, which define how a message is encoded for transport; and, optionally

* dialogues, which define rules over message sequences.

The framework provides one default protocol, called `default`. This protocol provides a bare bones implementation for an AEA protocol which includes a <a href="../api/protocols/default/message#defaultmessage-objects">`DefaultMessage`</a>  class and associated <a href="../api/protocols/default/serialization#defaultserializer-objects">`DefaultSerializer`</a> and <a href="..api/protocols/default/dialogues#defaultdialogues-objects">`DefaultDialogue`</a> classes.

Additional protocols - i.e. a new type of interaction - can be added as packages or generated with the <a href="../protocol-generator">protocol generator</a>. For more details on protocols also read the protocol guide <a href="../protocol">here</a>.

Protocol specific messages, wrapped in envelopes, are sent and received to other agents and services via connections.

### Connection

A <a href="../api/connections/base#connection-objects">`Connection`</a> wraps an SDK or API and provides an interface to network, ledgers and other services. Where necessary, a connection is responsible for translating between the framework specific `Envelope` with its contained `Message` and the external service or third-party protocol (e.g. `HTTP`).

The framework provides one default connection, called `stub`. It implements an I/O reader and writer to send messages to the agent from a local file.

Additional connections can be added as packages. For more details on connections also read the connection guide <a href="../connection">here</a>.

An AEA can run connections via a multiplexer.

### Multiplexer

<img src="/assets/multiplexer.png" alt="Multiplexer of an AEA" class="center" style="display: block; margin-left: auto; margin-right: auto;width:50%;">

The <a href="../api/multiplexer#multiplexer-objects">`Multiplexer`</a> is responsible for maintaining potentially multiple connections.

It maintains an <a href="../api/multiplexer#inbox-objects">`InBox`</a> and <a href="../api/multiplexer#outbox-objects">`OutBox`</a>, which are, respectively, queues for incoming and outgoing envelopes.

### Skill

<img src="/assets/skills.png" alt="Skills of an AEA" class="center" style="display: block; margin-left: auto; margin-right: auto;width:50%;">

<a href="../api/skills/base#skill-objects">`Skills`</a> are the core focus of the framework's extensibility as they implement business logic to deliver economic value for the AEA. They are self-contained capabilities that AEAs can dynamically take on board, in order to expand their effectiveness in different situations.

A skill encapsulates implementations of the three abstract base classes `Handler`, `Behaviour`, `Model`, and is closely related with the abstract base class `Task`:

* <a href="../api/skills/base#handler-objects">`Handler`</a>: each skill has none, one or more `Handler` objects, each responsible for the registered messaging protocol. Handlers implement AEAs' **reactive** behaviour. If the AEA understands the protocol referenced in a received `Envelope`, the `Handler` reacts appropriately to the corresponding message. Each `Handler` is responsible for only one protocol. A `Handler` is also capable of dealing with internal messages (see next section).
* <a href="../api/skills/base#behaviour-objects">`Behaviour`</a>: none, one or more `Behaviours` encapsulate actions which futher the AEAs goal and are initiated by internals of the AEA, rather than external events. Behaviours implement AEAs' **pro-activeness**. The framework provides a number of <a href="../api/skills/behaviours">abstract base classes</a> implementing different types of behaviours (e.g. cyclic/one-shot/finite-state-machine/etc.).
* <a href="../api/skills/base#model-objects">`Model`</a>: none, one or more `Models` that inherit from the `Model` can be accessed via the `SkillContext`.
* <a href="../api/skills/tasks#task-objects">`Task`</a>: none, one or more `Tasks` encapsulate background work internal to the AEA. `Task` differs from the other three in that it is not a part of skills, but `Task`s are declared in or from skills if a packaging approach for AEA creation is used.

A skill can read (parts of) the state of the the AEA (as summarised in the <a href="../api/context/base#agentcontext-objects">`AgentContext`</a>), and suggest actions to the AEA according to its specific logic. As such, more than one skill could exist per protocol, competing with each other in suggesting to the AEA the best course of actions to take. In technical terms this means skills are horizontally arranged.

For instance, an AEA who is trading goods, could subscribe to more than one skill, where each skill corresponds to a different trading strategy.  The skills could then read the preference and ownership state of the AEA, and independently suggest profitable transactions.

The framework places no limits on the complexity of skills. They can implement simple (e.g. `if-this-then-that`) or complex (e.g. a deep learning model or reinforcement learning agent).

The framework provides one default skill, called `error`. Additional skills can be added as packages. For more details on skills also read the skill guide <a href="../skill">here</a>.

### Main loop

The main agent loop performs a series of activities while the `Agent` state is not stopped.

* `act()`: this function calls the `act()` function of all active registered Behaviours.
* `react()`: this function grabs all Envelopes waiting in the `InBox` queue and calls the `handle()` function for the Handlers currently registered against the protocol of the `Envelope`.
* `update()`: this function dispatches the internal messages from the decision maker (described below) to the handler in the relevant skill.

## Next steps

### Recommended

We recommend you continue with the next step in the 'Getting Started' series:

- <a href="../aea-vs-mvc">AEA and web frameworks</a>

### Relevant deep-dives

Most AEA development focuses on developing the skills and protocols necessary for an AEA to deliver against its economic objectives.

Understanding protocols is core to developing your own agent. You can learn more about the protocols agents use to communicate with each other and how they are created in the following section:

- <a href="../protocol">Protocols</a>

Most of an AEA developer's time is spent on skill development. Skills are the core business logic commponents of an AEA. Check out the following guide to learn more:

- <a href="../skill">Skills</a>

In most cases, one of the available connection packages can be used. Occassionally, you might develop your own connection:

- <a href="../connection">Connections</a>

<br />


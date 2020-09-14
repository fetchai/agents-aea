The AEA framework consists of several core elements, some of which are required to run an AEA and others which are optional.

## The elements each AEA uses

<a href="../api/aea#aea-objects">`AEAs`</a> communicate asynchronously via `Envelopes`.

### Envelope

<img src="../assets/envelope.png" alt="Envelope of an AEA" class="center" style="display: block; margin-left: auto; margin-right: auto;width:50%;">

An <a href="../api/mail/base#envelope-objects">`Envelope`</a> is the core object with which agents communicate. It is a vehicle for `Messages` with five attributes:

* `to`: defines the destination address.

* `sender`: defines the sender address.

* `protocol_id`: defines the id of the `Protocol`.

* `message`: is a bytes field which holds the `Message` in serialized form.

* `Optional[context]`: an optional field to specify routing information in a URI.

<a href="../api/protocols/base#message-objects">`Messages`</a>  must adhere to a `Protocol`.

### Protocol

<a href="../api/protocols/base#protocol-objects">`Protocols`</a> define agent-to-agent as well as component-to-component interactions within agents. As such, they include:

* `Messages`, which define the representation;

* serialization logic, which define how a `Message` is encoded for transport; and, optionally

* `Dialogues`, which define rules over `Message` sequences.

The framework provides one default `Protocol`, called `default` (current version `fetchai/default:0.5.0`). This `Protocol` provides a bare-bones implementation for an AEA `Protocol` which includes a <a href="../api/protocols/default/message#aea.protocols.default.message">`DefaultMessage`</a>  class and associated <a href="../api/protocols/default/serialization#aea.protocols.default.serialization">`DefaultSerializer`</a> and <a href="../api/protocols/default/dialogues#aea.protocols.default.dialogues">`DefaultDialogue`</a> classes.

Additional `Protocols` - i.e. a new type of interaction - can be added as packages and generated with the <a href="../protocol-generator">protocol generator</a>. For more details on `Protocols` also read the `Protocol` guide <a href="../protocol">here</a>.

Protocol specific `Messages`, wrapped in `Envelopes`, are sent and received to other agents, agent components and services via `Connections`.

### Connection

A <a href="../api/connections/base#connection-objects">`Connection`</a> wraps an SDK or API and provides an interface to network, ledgers and other services. Where necessary, a `Connection` is responsible for translating between the framework specific `Envelope` with its contained `Message` and the external service or third-party protocol (e.g. `HTTP`).

The framework provides one default `Connection`, called `stub` (current version `fetchai/stub:0.9.0`). It implements an I/O reader and writer to send `Messages` to the agent from a local file.

Additional `Connections` can be added as packages. For more details on `Connections` also read the `Connection` guide <a href="../connection">here</a>.

An AEA can run `Connections` via a `Multiplexer`.

### Multiplexer

<img src="../assets/multiplexer.png" alt="Multiplexer of an AEA" class="center" style="display: block; margin-left: auto; margin-right: auto;width:50%;">

The <a href="../api/multiplexer#multiplexer-objects">`Multiplexer`</a> is responsible for maintaining potentially multiple `Connections`.

It maintains an <a href="../api/multiplexer#inbox-objects">`InBox`</a> and <a href="../api/multiplexer#outbox-objects">`OutBox`</a>, which are, respectively, queues for incoming and outgoing `Envelopes` from the perspective of `Skills`.

### Skill

<img src="../assets/skills.png" alt="Skills of an AEA" class="center" style="display: block; margin-left: auto; margin-right: auto;width:50%;">

<a href="../api/skills/base#skill-objects">`Skills`</a> are the core focus of the framework's extensibility as they implement business logic to deliver economic value for the AEA. They are self-contained capabilities that AEAs can dynamically take on board, in order to expand their effectiveness in different situations.

A `Skill` encapsulates implementations of the three abstract base classes `Handler`, `Behaviour`, `Model`, and is closely related with the abstract base class `Task`:

* <a href="../api/skills/base#handler-objects">`Handler`</a>: each `Skill` has none, one or more `Handler` objects, each responsible for the registered messaging `Protocol`. Handlers implement AEAs' **reactive** behaviour. If the AEA understands the `Protocol` referenced in a received `Envelope`, the `Handler` reacts appropriately to the corresponding `Message`. Each `Handler` is responsible for only one `Protocol`.
* <a href="../api/skills/base#behaviour-objects">`Behaviour`</a>: none, one or more `Behaviours` encapsulate actions which futher the AEAs goal and are initiated by internals of the AEA, rather than external events. Behaviours implement AEAs' **pro-activeness**. The framework provides a number of <a href="../api/skills/behaviours">abstract base classes</a> implementing different types of behaviours (e.g. cyclic/one-shot/finite-state-machine/etc.).
* <a href="../api/skills/base#model-objects">`Model`</a>: none, one or more `Models` that inherit from the `Model` can be accessed via the `SkillContext`.
* <a href="../api/skills/tasks#task-objects">`Task`</a>: none, one or more `Tasks` encapsulate background work internal to the AEA. `Task` differs from the other three in that it is not a part of `Skills`, but `Tasks` are declared in or from `Skills` if a packaging approach for AEA creation is used.

A `Skill` can read (parts of) the state of the the AEA (as summarised in the <a href="../api/context/base#agentcontext-objects">`AgentContext`</a>), and suggest actions to the AEA according to its specific logic. As such, more than one `Skill` could exist per `Protocol`, competing with each other in suggesting to the AEA the best course of actions to take. In technical terms this means `Skills` are horizontally arranged.

For instance, an AEA which is trading goods, could subscribe to more than one `Skill`, where each `Skill` corresponds to a different trading strategy.  The `Skills` could then read the preference and ownership state of the AEA, and independently suggest profitable transactions.

The framework places no limits on the complexity of `Skills`. They can implement simple (e.g. `if-this-then-that`) or complex (e.g. a deep learning model or reinforcement learning agent).

The framework provides one default `Skill`, called `error`. Additional `Skills` can be added as packages. For more details on `Skills` also read the `Skill` guide <a href="../skill">here</a>.

### Main loop

The main `AgentLoop` performs a series of activities while the `Agent` state is not stopped.

* `act()`: this function calls the `act()` function of all active registered Behaviours.
* `react()`: this function grabs all Envelopes waiting in the `InBox` queue and calls the `handle()` function for the Handlers currently registered against the `Protocol` of the `Envelope`.
* `update()`: this function dispatches the internal `Messages` from the decision maker (described below) to the handler in the relevant `Skill`.

## Next steps

### Recommended

We recommend you continue with the next step in the 'Getting Started' series:

- <a href="../aea-vs-mvc">AEA and web frameworks</a>

### Relevant deep-dives

Most AEA development focuses on developing the `Skills` and `Protocols` necessary for an AEA to deliver against its economic objectives.

Understanding `Protocols` is core to developing your own agent. You can learn more about the `Protocols` agents use to communicate with each other and how they are created in the following section:

- <a href="../protocol">Protocols</a>

Most of an AEA developer's time is spent on `Skill` development. `Skills` are the core business logic commponents of an AEA. Check out the following guide to learn more:

- <a href="../skill">Skills</a>

In most cases, one of the available `Connection` packages can be used. Occassionally, you might develop your own `Connection`:

- <a href="../connection">Connections</a>

<br />


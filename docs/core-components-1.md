The AEA framework consists of several core components, some required to run an AEA and others optional.

The following sections discuss the inner workings of the AEA framework and how it calls the code in custom packages (see <a href="https://en.wikipedia.org/wiki/Inversion_of_control" target="_blank">inversion of control</a> and a helpful comparison <a href="https://www.freecodecamp.org/news/the-difference-between-a-framework-and-a-library-bd133054023f/" target="_blank">here</a>). Whilst it is in principle possible to use parts of the framework as a library, we do not recommend it.

## The elements each AEA uses

### Envelope

<img src="../assets/envelope.jpg" alt="Envelope of an AEA" class="center" style="display: block; margin-left: auto; margin-right: auto;width:50%;">

<a href="../api/aea#aea-objects">`AEA`</a> objects communicate asynchronously via <a href="../api/mail/base#envelope-objects">`Envelopes`</a>.

An <a href="../api/mail/base#envelope-objects">`Envelope`</a> is the core object with which agents communicate. It is a vehicle for <a href="../api/protocols/base#message-objects">`Messages`</a> with five attributes:

* `to`: defines the destination address.

* `sender`: defines the sender address.

* `protocol_id`: defines the id of the `Protocol`.

* `message`: is a bytes field which holds the `Message` in serialized form.

* `Optional[context]`: an optional field to specify routing information in a URI.

<a href="../api/protocols/base#message-objects">`Messages`</a>  must adhere to a `Protocol`.

### Protocol

<a href="../api/protocols/base#protocol-objects">`Protocols`</a> define agent-to-agent as well as component-to-component interactions within AEAs. As such, they include:

* `Messages` defining the syntax of messages;

* `Serialization` defining how a `Message` is encoded for transport; and, optionally

* `Dialogues`, which define rules over `Message` sequences.

The framework provides one default `Protocol`, called `default` (current version `fetchai/default:1.0.0`). This `Protocol` provides a bare-bones implementation for an AEA `Protocol` which includes a <a href="../api/protocols/default/message#packages.fetchai.protocols.default.message">`DefaultMessage`</a>  class and associated <a href="../api/protocols/default/serialization#packages.fetchai.protocols.default.serialization">`DefaultSerializer`</a> and <a href="../api/protocols/default/dialogues#packages.fetchai.protocols.default.dialogues">`DefaultDialogue`</a> classes.

Additional `Protocols`, for new types of interactions, can be added as packages. For more details on `Protocols` you can read the <a href="../protocol">protocol guide</a>. To learn how you can easily automate protocol definition, head to the guide for the <a href="../protocol-generator">protocol generator</a>.

Protocol specific `Messages`, wrapped in `Envelopes`, are sent and received to other agents, agent components and services via `Connections`.

### Connection

A <a href="../api/connections/base#connection-objects">`Connection`</a> wraps an SDK or API and provides an interface to networks, ledgers or other services. Where necessary, a `Connection` is responsible for translating between the framework specific `Envelope` with its contained `Message` and the external service or third-party protocol (e.g. `HTTP`).

The framework provides one default `Connection`, called `stub` (current version `fetchai/stub:0.21.0`). It implements an I/O reader and writer to send `Messages` to the agent from a local file.

Additional `Connections` can be added as packages. For more details on `Connections` read the <a href="../connection"> `Connection` guide </a>.

An AEA runs and manages `Connections` via a `Multiplexer`.

### Multiplexer

<img src="../assets/multiplexer.png" alt="Multiplexer of an AEA" class="center" style="display: block; margin-left: auto; margin-right: auto;width:50%;">

The <a href="../api/multiplexer#multiplexer-objects">`Multiplexer`</a> is responsible for maintaining (potentially multiple) `Connections`.

It maintains an <a href="../api/multiplexer#inbox-objects">`InBox`</a> and <a href="../api/multiplexer#outbox-objects">`OutBox`</a>, which are, respectively, queues for incoming and outgoing `Envelopes` from the perspective of `Skills`.

### Skill

<img src="../assets/skills.jpg" alt="Skills of an AEA" class="center" style="display: block; margin-left: auto; margin-right: auto;width:50%;">

<a href="../api/skills/base#skill-objects">`Skills`</a> are the core focus of the framework's extensibility as they implement business logic to deliver economic value for the AEA. They are self-contained capabilities that AEAs can dynamically take on board, in order to expand their effectiveness in different situations.

A `Skill` encapsulates implementations of the three abstract base classes `Handler`, `Behaviour`, `Model`, and is closely related with the abstract base class `Task`:

* <a href="../api/skills/base#handler-objects">`Handler`</a>: each `Skill` has zero, one or more `Handler` objects. There is a one-to-one correspondence between `Handlers` and the protocols in an AEA (also known as the _registered protocols_). Handlers implement AEAs' **reactive** behaviour. If an AEA understands a `Protocol` referenced in a received `Envelope` (i.e. the protocol is registered in this AEA), this envelope is sent to the corresponding `Handler` which executes the AEA's reaction to this `Message`. 
* <a href="../api/skills/base#behaviour-objects">`Behaviour`</a>: a `skill` can have zero, one or more `Behaviours`, each encapsulating actions which further the AEAs goal and are initiated by internals of the AEA rather than external events. Behaviours implement AEAs' **pro-activeness**. The framework provides a number of <a href="../api/skills/behaviours">abstract base classes</a> implementing different types of simple and composite behaviours (e.g. cyclic, one-shot, finite-state-machine, etc), and these define how often and in what order a behaviour and its sub-behaviours must be executed.
* <a href="../api/skills/base#model-objects">`Model`</a>: zero, one or more `Models` that inherit from the `Model` abstract base class and are accessible via the `SkillContext`.
* <a href="../api/skills/tasks#task-objects">`Task`</a>: zero, one or more `Tasks` encapsulate background work internal to the AEA. `Task` differs from the other three in that it is not a part of `Skills`, but `Tasks` are declared in or from `Skills` if a packaging approach for AEA creation is used.

A `Skill` can read (parts of) an AEA's state (as summarised in the <a href="../api/context/base#agentcontext-objects">`AgentContext`</a>), and suggests actions to the AEA according to its specific logic. As such, more than one `Skill` could exist per `Protocol`, competing with each other in suggesting to the AEA the best course of actions to take. In technical terms, this means `Skills` are horizontally arranged.

For instance, an AEA which is trading goods, could subscribe to more than one `Skill`, where each corresponds to a different trading strategy.

The framework places no limits on the complexity of `Skills`. They can implement simple (e.g. `if-this-then-that`) logic or be complex (e.g. a deep learning model or reinforcement learning agent).

The framework provides one default `Skill`, called `error`. Additional `Skills` can be added as packages. For more details on `Skills` head over to the <a href="../skill"> `Skill` guide </a>.

### Agent loop

The <a href="../api/agent_loop#baseagentloop-objects">`AgentLoop`</a> performs a series of activities while the `AEA` state is not `stopped`.

* it calls the `act()` function of all active registered `Behaviours` at their respective tick rate.
* it grabs all Envelopes waiting in the `InBox` queue and calls the `handle()` function for the `Handlers` currently registered against the `Protocol` of the `Envelope`.
* it dispatches the internal `Messages` from the decision maker (described below) to the handler in the relevant `Skill`.

The <a href="../api/agent_loop#baseagentloop-objects">`AgentLoop`</a> and <a href="../api/multiplexer#multiplexer-objects">`Multiplexer`</a> are decoupled via the <a href="../api/multiplexer#inbox-objects">`InBox`</a> and <a href="../api/multiplexer#outbox-objects">`OutBox`</a>, and both are maintained by the <a href="../api/runtime#baseruntime-objects">`Runtime`</a>.

## Next steps

### Recommended

We recommend you continue with the next step in the 'Getting Started' series:

- <a href="../aea-vs-mvc">AEA and web frameworks</a>

### Relevant deep-dives

Most AEA development focuses on developing the `Skills` and `Protocols` necessary for an AEA to deliver against its economic objectives.

Understanding `Protocols` is core to developing your own agent. You can learn more about the `Protocols` agents use to communicate with each other and how they are created in the following section:

- <a href="../protocol">Protocols</a>

Most of an AEA developer's time is spent on `Skill` development. `Skills` are the core business logic components of an AEA. Check out the following guide to learn more:

- <a href="../skill">Skills</a>

In most cases, one of the available `Connection` packages can be used. Occasionally, you might develop your own `Connection`:

- <a href="../connection">Connections</a>

<br />


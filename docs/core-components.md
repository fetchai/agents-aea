# Core Components

AEAs can be made from various components, much like legos, and these components can be of differing types. Below are some of the more important types of components an agent can have.   

## Skill

A **Skill** is an isolated, self-contained, (and preferably atomic) functionality that AEAs can take on board to expand their capability. Skills contain the proactive and reactive behaviour that ultimately makes it possible for an AEA to deliver economic value to its owner.  

A Skill encapsulates implementations of three base classes `Handler`, `Behaviour`, `Model`, and is closely related with `Task`:

- Handler: Handlers implement AEAs' **reactive** behaviour. If an AEA understands a protocol referenced in a received `Envelope`, this envelope is sent to the corresponding handler which executes the AEA's reaction to this message.
- Behaviour: Behaviours implement AEAs' **proactiveness**, encapsulating actions which further an AEA's goals, and are initiated by internals of the AEA rather than external events. 
- Model: Encapsulate arbitrary objects and is made available to all components of the skill.
- Task: Tasks encapsulate background work internal to the AEA. 

A skill can read (parts of) an AEA's state and propose actions to the AEA according to its specific logic. As such, more than one skill could exist per protocol, competing with each other in suggesting to the AEA the best course of actions to take. 

For instance, an AEA which is trading goods, could subscribe to more than one skill, where each corresponds to a different trading strategy.

The framework places no limits on the complexity of `Skills`. They can implement simple (e.g. if-this-then-that) logic or be complex (e.g. a deep learning model or reinforcement learning agent).

The framework provides one default `error` skill. Additional `Skills` can be added as packages. For more details on skills, head over to the <a href="../skill"> `Skill` guide </a>.

## Protocol

A **Protocol** defines the structure and nature of an interaction that can happen between agents, or between components of an agent. You can think of a protocol as the language that two agents speak and a skill for this protocol as a particular way of speaking this language. From a game-theoretic viewpoint, a protocol defines the rules of a game and a skill for this protocol defines a particular strategy for playing this game. 

Protocols define agent-to-agent as well as component-to-component interactions within AEAs. As such, they include:

- `Messages`: defining the syntax of messages.
- `Serialization`: defining how a message is encoded for transport.
- `Dialogues`: defines rules over sequences of messages.

The framework provides one `default` protocol. This protocol provides a bare-bones implementation which includes a <a href="../api/protocols/default/message#packages.fetchai.protocols.default.message">`DefaultMessage`</a>  class and associated <a href="../api/protocols/default/serialization#packages.fetchai.protocols.default.serialization">`DefaultSerializer`</a> and <a href="../api/protocols/default/dialogues#packages.fetchai.protocols.default.dialogues">`DefaultDialogue`</a> classes.

Additional protocols for new types of interactions, can be added as packages. For more details on protocols, you can read the <a href="../protocol">protocol guide</a>. To learn how you can easily automate protocol definition, head to the guide for the <a href="../protocol-generator">protocol generator</a>.

Protocol specific messages, wrapped in `Envelopes`, are sent and received to other agents, agent components and services via **Connections**.

## Connection

**Connections** act as interfaces between an agent and the outside world. As such, a connection allows the agent to communicate with some entity outside of it, for example, another agent, a traditional HTTP server, a database, a reinforcement learning training environment, a blockchain, etc.

Where necessary, a Connection is responsible for translating between the framework specific `Envelope` with its contained message and the external service or third-party protocol (e.g. HTTP).

The framework provides one default `stub` connection. It implements an I/O reader and writer to send messages to the agent from a local file.

Additional connections can be added as packages. For more details on `Connections` read the <a href="../connection">`Connection` guide</a>.
This glossary defines a number of terms commonly used across the documentation. 
The further information the concepts links provided to the respective sections 
in the guide or to external resources are provided.  
For the definitions of framework components one may consult the API docs.

* **Agent**: An agent is one that acts as an instrument on behalf of its owner 
or another agent to achieve a result.  
[<a href="https://www.merriam-webster.com/dictionary/agent" target="_blank">more</a>]

* **Software Agent**: a software agent is a computer program that acts on behalf
of an entity (e.g. individual, organisation, business). 
[<a href="https://en.wikipedia.org/wiki/Software_agent" target="_blank">more</a>]

* **AEA (Autonomous Economic Agent)**: An AEA is "an intelligent agent acting on
an owner's behalf, with limited or no interference, and whose goal is to 
generate economic value to its owner". AEAs are a special type of agent.
[<a href="../index">more</a>]

* **MAS (Multi-agent system)**: A MAS is a system that is inhabited by agents 
who can interact with their environment and other agents in the system through 
the use of decision-making logic. 
[<a href="https://en.wikipedia.org/wiki/Multi-agent_system" target="_blank">more</a>]

* **ACN (Agent Communication Network)**: The ACN is a peer-to-peer communication
network for autonomous economic agents. 
[<a href="../acn/">more</a>]

* **Distributed**: Distributed systems or computing refers to networks whose 
nodes are physically separated, and who may be used to solve problems 
efficiently by dividing their workload. 
[<a href="https://en.wikipedia.org/wiki/Distributed_computing" target="_blank">more</a>]

* **Decentralized**: Decentralized systems or computing refers to networks whose
nodes are owned by different users, which may be used for peer-to-peer 
communication without a third-party intermediary acting as a central authority.
[<a href="https://en.wikipedia.org/wiki/Decentralized_computing" target="_blank">more</a>]

* **Skill**: A Skill encapsulates implementations Handler, Behaviour and Model, 
and may include any number of each of these components. 
[<a href="../skill/">more</a>]
    * **Handler**: Handlers are used to manage incoming messages. They 
    constitute the means for an AEA to respond to input from its environment.
    * **Behaviour**: Behaviour encapsulates actions which further the AEAs goal 
    and are initiated by internals of the AEA rather than external events. They 
    constitute an activity that an AEA can proactively engage in.
    * **Model**: A Model is a dynamic data structure that manages data, logic 
    and rules of the application.

* **Task**: Encapsulate skill components that are scheduled for asynchronous 
execution. They are background processes that enable concurrency in the system,
which is a necessity for independence be their behaviour and decision-making. 
[<a href="../skill/#taskspy">more</a>]

* **Context**: The context provides access to the objects in other parts of the
implementation. More specifically, the:
    * **AgentContext**: Provides read access to relevant objects of the agent 
    for the skills. Such information includes public keys and addresses of the 
    AEA. It also provides access to the OutBox.
    * **SkillContext**: The skill has a SkillContext object which is shared by 
    all Handler, Behaviour, and Model objects. The skill context also has a link
    to the AgentContext.

* **Ledger**: A ledger is a record in which transactions are recorded. With
regard to cryptocurrencies these are distributed ledgers which contain 
information on ownership. 
[<a href="../ledger-integration/">more</a>]

* **Decision Maker**: The DecisionMaker can be thought of as a Wallet manager 
plus "economic brain" of the AEA. It is responsible for the AEAs crypto-economic
security and goal management. The decision maker is the only component with 
access to the Wallet's private keys. In its simplest form, the decision maker 
acts like a Wallet with a Handler, which allow it to react to messages it 
receives.
[<a href="../decision-maker/">more</a>]

* **Envelopes**: AEA objects communicate asynchronously via Envelopes. An 
Envelope is the core object with which agents communicate. It is a vehicle for 
Messages.
[<a href="../core-components-1/#envelope">more</a>]

* **Protocol**: Protocols define agent-to-agent as well as 
component-to-component interactions within AEAs. As such, they include:
Messages; Serialization; Dialogues (rules over Message sequences). 
Protocol-specific messages, wrapped in Envelopes, are sent and received to other
agents, agent components and services via connections.
[<a href="../protocol/">more</a>]

* **Connection**: A Connection wraps an SDK or API and provides an interface to 
networks, ledgers or other services. Where necessary, a Connection is 
responsible for translating between the framework specific Envelope with its 
contained Message and the external service or third-party protocol (e.g. HTTP).
[<a href="../connection/">more</a>]

* **Multiplexer**: The Multiplexer is responsible for maintaining connections. 
It maintains an InBox and OutBox, which are, respectively, queues for incoming 
and outgoing Envelopes from the perspective of Skills.
[<a href="../core-components-1/#multiplexer">more</a>]

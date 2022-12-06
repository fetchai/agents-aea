The AEA framework development is guided by the following _8  design principles_:

* **Accessibility**: ease of use.
* **Modularity**: encourages module creation, sharing and reuse.
* **Openness**: easily extensible with third-party libraries.
* **Conciseness**: conceptually simple.
* **Value-driven**: drives immediate value.
* **Low entry barriers**: leverages existing programming languages and web protocols.
* **Safety**: economically safe for the user.
* **Goal-alignment**: seamless facilitation of users' preferences and goals.

!!! info

    The Framework is based around the concept of asynchronous message passing and uses an actor-like design paradigm. Messages are the primary means of communication between the Framework components as well as agents. In this respect, messages are directed towards a recipient which can be external or internal to the agent.

The Framework aims to allow for modularity and reuse. The developer develops some packages or reuses those packages developed by others and then places them in context to each other in an AEA. The Framework then calls the code in the packages. Unlike libraries, it is the Framework that runs and calls the code by making use of inversion of control. 

!!! note

    Currently, the Framework is implemented in the Python programming language. However, implementation in other languages is feasible too and importantly, it is fully interoperable with any language stack provided the protocols are implemented correctly. 

The framework offers auxiliary tools and services, including a command line interface (CLI), a protocol generator to generate protocols' code from their specifications, test tools, a registry for framework packages, and a desktop app to run finished agents. In its design, the framework makes no assumptions about the type of agents implemented with it. 

The Framework architecture has two distinctive parts:

1. A **core** that is developed by the Fetch.ai team as well as external contributors.
2. **Extensions** (i.e. packages) developed by any developer.

The framework defines the _four main components_ which make up an agent:

1. **Skills** encapsulate the logic that delivers economic value to the AEA. These are the core focus of the framework's extensibility as they implement business logic to deliver economic value for the AEA and its owner. Skills are treated like black boxes by the framework and can contain simple conditional logic or advanced reinforcement learning algorithms, for instance. 

2. **Connections** provide interfaces for the agent to connect with the outside world. These wrap SDKs or APIs and provide an interface to network, ledgers and other services. Where necessary, a connection is responsible for translating between the framework specific protocols and the external service or third-party protocol (e.g. HTTP).

3. **Protocols** define agent-to-agent as well as component-to-component interactions within agents. As such, they include messages, which define the representation, serialization logic, how a message is encoded for transport, and, dialogues, which define rules over message sequences for a given protocol.

4. **Contracts** wrap (access to) smart contracts for Fetch.ai and third-party decentralized ledgers. In particular, they provide wrappers around the API or ABI of a smart contract and its byte code.

Together, these four components can be utilized to establish interaction protocols between entities. 

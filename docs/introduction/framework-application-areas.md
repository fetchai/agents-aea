The environment in which agents may operate features the following features:

* **Decentralization**. 
* **Attraction of multiple stakeholders** who are represented by AEAs populating this environment and which:

    - interact autonomously, and 
    - communicate with one another directly via a P2P network.

## Areas of application

We identify a number of application areas for AEA-based solutions. This list is by no means comprehensive. In fact, we are most excited about applications which we have not thought of before. For instance:

1. **Inhabitants**: agents representing objects in the IoT (Internet of Things) space. 

    !!! example

        For example, AEAs paired with real world hardware devices such as drones, laptops, heat sensors, etc. An example is a [thermometer agent](https://docs.fetch.ai/aea/thermometer-skills).

2. **Interfaces**: facilitation agents which provide the necessary API interfaces for interaction between existing (Web 2.0) and new (Web 3.0) economic models. 

    !!! example

        An example is an AEA with [HTTP connection and skill](https://docs.fetch.ai/aea/http-connection-and-skill) who has the capability to communicate using HTTP.

3. **Pure software**: software agents living in the digital space that interact with interface agents and others.

4. **Digital data sales agents**: software agents that attach to data sources and sell it via the open economic framework. An example can be found [here](https://docs.fetch.ai/aea/ml-skills).

5. **Representative**: an agent which represents an individual's activities on the Fetch.ai network. An example can be found [here](https://docs.fetch.ai/aea/tac-skills).

In the _short-term_, we see AEAs primarily deployed in three main areas:

1. **Off-load repetitive tasks**: AEAs can automate well-defined processes in different domains such as supply chain, mobility and finance, etc.

2. **Micro-transactions**: AEAs make it economically viable to execute trades which involve small value transfers. This is particularly relevant in areas where there is a (data) supply side constituted of many small actors and a single demand side.

3. **Wallet agents**: AEAs can simplify interactions with blockchains for end users. For instance, they can act as "smart wallets" which optimize blockchain interactions on behalf of the user.

!!! warning

    Multi-agent systems (MAS) enabled by the AEA Framework are technological agent-based solutions to real problems and, although there is some overlap, the Framework is not designed from the outset to be used as an agent-based modeling software where the goal is scientific behavioral observation rather than practical economic gain.

    Moreover, single-agent applications are also supported. In light of such considerations, agent frameworks and MAS have only found limited real-world applications despite being developed in the research community for multiple decades. We hope that the AEA Framework will see adoption in and contributions from the wider MAS community. This Framework can be adopted in various application scenarios considering that the overarching theme encompassing all these application areas is the coding of interactions between different economic entities.  

A more general list of possible applications areas for AEA-based solutions can be the following:

1. **Automate user interactions with blockchains**: AEAs can be used to automate a user's interactions with the blockchain. The advantage is that the AEA can consistently and efficiently carry out the interactions. 

    !!! example

        The Autonomous Hegician, for example, employs an AEA to automate option management.

2. **Enhance user interactions with blockchains**: users are heavily constrained when using blockchains by the web clients they have access to and their own abilities. An AEA can interact with a blockchain much faster, more securely and with more (on-chain) protocols than a human ever could.

3. **Abstract ledger specifics for developers**: for developers the framework abstracts away many ledger specifics. It allows developers to reuse plugins for specific ledgers which provide a common interface, thereby making it straightforward to write cross-ledger applications.

4. **Supply off-chain data to blockchains**: transaction based blockchain systems rely on constant external input to progress. As a result oracles take an important role for many on-chain applications. AEAs can be used to operate oracles. Since AEAs can utilize off-chain protocols they are the ideal framework to develop resilient oracles.

5. **Bridge different ecosystems**: an AEA can bridge disconnected ecosystems. For instance, it can wrap a public API to serve data to other agents in agent native protocols, or expose its information via a server.

6. **Enable agent to agent interactions**: AEAs shine when they are used to building multi-stakeholder agent-based solutions. 

    !!! example

        Some examples we and other teams worked on include supply chain, mobility and decentralized manufacturing marketplaces. AEAs can also be connected to Layer 2 solutions like state channels (e.g. Perun, State Channels) and rollups (e.g. Optimism, ZkSync) to enable faster and cheaper transactions.

7. **Simplify protocol development**: a side effect of the AEA's protocol generator is that it allows developers to easily define new interaction protocols. In fact, with some extra effort this tool could be made available to everyone, it will become easier and easier to develop new protocols.

8. **Simulate multi-stakeholder economies**: although the framework was not developed for simulations and agent-based modeling, it does lend itself under certain scenarios for this purpose. In particular, when no synchronization between agents is required and the simulation is meant to be as-close-to-reality-as-possible then the AEA framework can be used for this purpose. The multi-agent manager lets developers spin up many agents in a programmatic and dynamic way.

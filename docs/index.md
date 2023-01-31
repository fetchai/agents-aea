# AEA Framework Documentation

!!! target "Vision"
    Our aim with the AEA framework is to enable businesses of all sizes, from independent developers to large corporations and consortiums, to create and deploy agent-based solutions in various domains, thus contributing to and advancing a decentralized mixed-initiative economy: one whose actors are both humans and machines.

## What is an AEA?

!!! info "Definition"
    An Autonomous Economic Agent (AEA) is an intelligent agent that acts on its owner's behalf, with limited or no interference, and whose goal is to generate economic value for its owner.

Breaking it down:

**AGENT**: An AEA represents an individual, organisation or object and looks after their interests.

**AUTONOMOUS**: AEAs operate independently of constant input from their owners and act autonomously to achieve their goals.

**ECONOMIC**: AEAs have a narrow and specific focus: creating economic value for their owner.

## What Can You Do with AEAs?

[//]: # (AEAs have the potential of being the next "apps", by enabling p2p. Most importantly,   )

Some examples of the kinds of applications you can build with AEAs:

**Automation**

:   AEAs can automate well-defined processes in different domains, such as supply chain, mobility, finance, ...

**Micro-transactions**

:   AEAs make it economically viable to execute trade involving small values. An example is use-cases with many small sellers (e.g. of data) on the supply side.

**Wallet**

:   AEAs can simplify interactions with blockchains. By acting as "smart wallets", they can hide away the majority of the complexities involved in using blockchains for end users.

**IoT**

:   Agents representing objects in the IoT (Internet of Things) space. For example, AEAs paired with hardware devices such as drones, laptops, heat sensors, etc., providing control and receiving data from the device. An example is a <a href="../thermometer-skills"> thermometer agent</a>.

**Web 2.0 <--> Web 3.0 interface**

:   Agents that interface and bridge the gap between existing (Web 2.0) and new (Web 3.0) economic models. An example is an <a href="../http-connection-and-skill"> AEA that communicates with HTTP clients/servers</a>.

**Traders**

:   Agents with access to some data sources that sell the data, access to the data, or access to the usage of the data. An example is an <a href="../ml-skills">AEA that continuously sells data to another AEA</a>, who in turn uses it to improve their reinforcement learning model.

## Who is This For?

The AEA technology is for anyone who wants to build or contribute to a "mixed-initiative economy": one whose actors are humans as well as machines. 

This includes (amongst others): developers, data scientists and machine learning experts, economists, students, academics and researchers (in Artificial Intelligence, Machine Learning, Multi-Agent Systems, etc), engineers, and so forth.

## The AEA Framework

The AEA framework is a development suite which equips you with an efficient and accessible set of tools for building and running AEAs and their components. 

The framework attempts to make agent development as straightforward an experience as possible, similar to what popular web frameworks enable for web development.

Some of the characteristics of the AEA framework are:

- **Python**: Using Python as an approachable programming language improves the on-boarding for those who just want to get started with agent development.
- **Open source**: The framework is open source and licensed under [Apache 2.0](https://github.com/fetchai/agents-aea/blob/main/LICENSE).
- **Modular**: Modularity is at the heart of the framework's design. This makes it easy to extend the framework, add new functionality, and re-use others' contributions, therefore reducing the development cost.
- **Blockchain ready**: Integration with blockchains is baked into the framework, enabling the creation of agents that take full advantage of the blockchain technology.
- **Modern**: The framework is built from and can be integrated with the latest technologies (e.g. asynchronous programming, blockchains and smart contracts, machine-learning ready, ...).

## The Ecosystem

Though they can work in isolation, AEAs are truly valuable when situated in a wider ecosystem consisting of tools and infrastructure that enable them to cooperate and compete, and interact with services as well as traditional or modern systems. These include:

- The <a href="acn">Agent Communication Network (ACN)</a>: A peer-to-peer communication infrastructure that enables AEAs to directly communicate with one another without any intermediaries.
- The <a href="simple-oef">sOEF</a>: A search and discovery system allowing AEAs to register themselves and the services they offer, and search for agents who offer specific services.
- The <a href="https://aea-registry.fetch.ai/" target="_blank">AEA Registry</a>: A space to store and share AEAs or individual agent components for anyone to find and use.
- Blockchains: AEAs can use blockchains as a financial and commitment layer. Each <a href="ledger-integration">ledger plug-in</a> provided by the framework adds the ability for AEAs to interact with a specific ledger, such as the <a href="https://docs.fetch.ai/ledger_v2/">Fetch.ai blockchain</a> or <a href="https://ethereum.org/en/" target="_blank">Ethereum</a>.
- Smart Contracts: <a href="contract">Contract packages</a> are wrappers around smart contracts that allow AEAs to interact with them through a common interface.

## How to get involved?

There are many ways for you to get involved. You can create agents, develop new agent components, extend existing components, and contribute to the development of the framework or other related tools. Please refer to the <a href="https://github.com/fetchai/agents-aea/blob/main/CONTRIBUTING.md">Contribution</a> and <a href="https://github.com/fetchai/agents-aea/blob/main/DEVELOPING.md">Development</a> guides.

## Next Steps

To get started developing your own AEA, check out the <a href="quickstart">getting started</a> section.

To learn more about some of the distinctive characteristics of agent-oriented development, check out the guide on <a href="agent-oriented-development">agent-oriented development</a>.

If you would like to develop an AEA in a language different to Python then check out our <a href="language-agnostic-definition">language agnostic AEA definition</a>.

If you want to run a demo, check out the <a href="demos">demo guides</a>.

## Help us Improve

!!! note
    This developer documentation is a work in progress. If you spot any errors please open an issue on <a href="https://github.com/fetchai/agents-aea" target="_blank">Github</a> or contact us in the <a href="https://discord.com/invite/btedfjPJTj" target="_blank">developer Discord channel</a>.

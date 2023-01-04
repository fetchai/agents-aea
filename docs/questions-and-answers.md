??? question "What is an AEA?"
    AEA stands for "Autonomous Economic Agent". An AEA can represent an individual, organisation or object and looks after its owner's interests. AEAs act independently of constant user input and autonomously execute actions to achieve their prescribed goals. Their purpose is to create economic value for their owners.

??? question "How do AEAs talk to each other when they do not know each other?"
    For an Autonomous Economic Agent (AEA) to talk to other AEAs, it first needs to find them. Once it does, it should ensure that they both use the same protocol for communication, and if so, they then have to send messages to each other.

    The AEA framework, together with some of the services it provides, address all three problems. You can read more about search and discovery <a href="../oef-ledger/">here</a>, protocols <a href="../core-components-1/">here</a>, and the Agent Communication Network (ACN) <a href="../acn/">here</a>.

??? question "How does an AEA use blockchain?"
    The AEA framework enables agents to interact with blockchains to settle transactions. Currently, the framework has native support for three different networks: _Fetch.ai_, _Ethereum_ and _Cosmos_.

    You can read more about the framework's integration with the different blockchains <a href="../ledger-integration/">here</a> and gain a high level overview <a href="../oef-ledger/">here</a>.

??? question "How does one install third party libraries?"
    The framework supports the use of third-party libraries hosted on <a href="https://pypi.org" target="_blank">PyPI</a>. You can directly reference the external dependencies of an AEA package (e.g. skill) in its configuration file. From inside an AEA's project directory, the `install` command can be used to install all the dependencies of the AEA listed in the configuration files of any of it's packages.

??? question "How does one connect to a database?"
    You have two options to connect to a database: using the built-in storage solution or using a custom ORM (object-relational mapping) library and backend.

    The use of the built-in storage is explained <a href="../generic-storage/">here</a>. For a detailed example of how to use an ORM, follow the <a href="../orm-integration/">ORM guide</a>.

??? question "How does one connect a frontend?"
    There are multiple options. The most obvious is using an HTTP server connection and creating a client that communicates with this connection. 

    You can find a more detailed discussion <a href="../connect-a-frontend/">here</a>.

??? question "Is the AEA framework ideal for agent-based modelling?"
    The goal of agent-based modelling (ABM) is to study the unknown (often complex) behaviour of systems comprised of agents with known (much simpler) behaviour. ABM is a popular technique for studying biological and social systems. Despite some similarities between ABM and the AEA framework, the two have fundamentally different goals. ABM's goal is not the design of agents or solving specific practical or engineering problems. Although it would be potentially possible, it would likely be inefficient to use the AEA framework for that kind of problem. 

    You can find more details on the application areas of the AEA framework <a href="../app-areas/">here</a>.

??? question "When a new AEA is created, is the `vendor` folder populated with some default packages?"
    All AEA projects by default hold the `fetchai/default:1.1.6`, `fetchai/state_update:1.1.6` and `fetchai/signing:1.1.6` protocols. These (as all other packages installed from the registry) are placed in the `vendor` folder. 

    You can find more details about the file structure <a href="../package-imports/">here</a>.

??? question "Is there a standardization for private key files?"
    Currently, the private keys are stored in `.txt` files. This is temporary and will be improved soon.

??? question "How to use the same protocol in different skills?"
    The details of envelope/message routing by the AEA framework are discussed in <a href="../message-routing/">this guide</a>.

??? question "Why does the AEA framework use its own package registry?"
    AEA packages could be described as personalized plugins for the AEA runtime. They are not like a library - they have no direct use outside the context of the framework - and therefore are not suitable for distribution via <a href="https://pypi.org/" target="_blank">PyPI</a>.

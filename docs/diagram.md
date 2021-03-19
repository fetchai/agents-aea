The framework has two distinctive parts.

- A **core** that is developed by the Fetch.ai team as well as external contributors.
- **Extensions** (also known as **packages**) developed by any developer.

Currently, the framework supports four types of packages which can be added to the core as modules:

- <a href="../skill">Skills</a> encapsulate logic that deliver economic value to the AEA. Skills are the main focus of the framework's extensibility. 
- <a href="../protocol">Protocols</a> define the structure of agent-to-agent and component-to-component interactions (messages and dialogues) for agents.
- <a href="../connection">Connections</a> provide interfaces for the agent to connect with the outside world. They wrap SDKs or APIs and provide interfaces to networks, ledgers and other services.
- <a href="../contract">Contracts</a> wrap smart contracts for Fetch.ai and third-party decentralized ledgers.

The following figure illustrates the framework's architecture:

<img src="../assets/simplified-aea.jpg" alt="Simplified illustration of an AEA" class="center" style="display: block; margin-left: auto; margin-right: auto;width:100%;">


The execution is broken down in more detail below:

<img src="../assets/execution.jpg" alt="Execution of an AEA" class="center" style="display: block; margin-left: auto; margin-right: auto;width:100%;">

The agent operation breaks down into three parts:

* **Setup**: calls the `setup()` method of all registered resources
* **Operation**:
    * Agent loop (Thread 1 - Asynchronous agent loop):
        * `react()`: this function grabs all Envelopes waiting in the `InBox` queue and calls the `handle()` method on the Handler(s) responsible for them. 
        * `act()`: this function calls the `act()` method of all registered Behaviours. 
        * `update()`: this function enqueues scheduled tasks for execution with the `TaskManager` and executes the decision maker.
    * Task loop (Thread 2- Synchronous): executes available tasks
    * Decision maker loop (Thread 3- Synchronous): processes internal messages
    * Multiplexer (Thread 4 - Asynchronous event loop): processes incoming and outgoing messages across several connections asynchronously.
* **Teardown**: calls the `teardown()` method of all registered resources


To prevent a developer from blocking the main loop with custom skill code, an execution time limit is  applied to every `Behaviour.act` and `Handler.handle` call.

By default, the execution limit is set to `0` seconds, which disables the feature. You can set the limit to a strictly positive value (e.g. `0.1` seconds) to test your AEA for production readiness. If the `act` or `handle` time exceed this limit, the call will be terminated.

An appropriate message is added to the logs in the case of some code execution being terminated.


<br />

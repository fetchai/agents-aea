
!!!	Note	
	Work in progress.

## Design principles

* Accessibility: easy to use.
* Modularity: encourages module creation and sharing.
* Openness: easily extensible with third party libraries.
* Conciseness: conceptually simple.
* Value-driven: drives immediate value for some use case.
* Low entry barriers: leverages existing languages and protocols.
* Safety: safe for the user (economically).
* Goal alignment: seamless facilitation of user preferences and goals.

<br />


## Architecture diagram

<center>![The AEA Framework Architecture](assets/framework-architecture.png)</center>


## Core components

### Protocol

Protocols define how messages are represented and encoded for transport. They also define the rules to which messages have to adhere in a message sequence. 

For instance, a protocol may contain messages of type `START` and `FINISH`. From there, the rules could prescribe that a message of type `FINISH` must be preceded by a message of type `START`.

The `Message` class in the `protocols/base.py` module provides an abstract class with all the functionality a derived Protocol message class requires for a custom skill, such as basic message generating and management functions and serialisation details.

### Connection

A connection wraps an external SDK or API and manages the messaging. It allows the agent to connect to an external service which has a Python SDK or API. 

### Skill

Skills deliver economic value to the AEA by allowing an agent to encapsulate and call any kind of code. It encapsulates Handlers, Behaviours, and Tasks.

* Handler: each skill has a single Handler which is responsible for the registered protocol messaging. By understanding the requirements contained in Envelopes, the Handler reacts appropriately to message requests.
* Behaviour: one or more Behaviours encapsulate sequences of actions that cause interactions with other agents initiated by the framework. 
* Task: one or more Tasks encapsulate background work internal to the agent.

### MailBox

A MailBox contains InBox and OutBox queues which manage Envelopes.

### Envelope

An Envelope is the core object which agents use to communicate with each other. It has four attribute parameters:

* `to`: defines the destination address.

* `sender`: defines the sender address.

* `protocol_id`: defines the id of the protocol.

* `message`: is a bytes field which holds the message in serialized form.

The Envelope encodes and decodes messages.


## Agent 

### Main loop

The `_run_main_loop()` function in the `Agent` class performs a series of activities while the `Agent` state is not stopped.

* `act()`: this function calls the `act()` function of all registered Behaviours.
* `react()`: this function grabs all Envelopes waiting in the InBox queue and calls the `handle()` function on them.
* `update()`: this function loops through all the Tasks and executes them.

## Resources 

The `Resources` class implements all resources for an agent. These come in the form of registries.

The specific classes are in the `registries/base.py` module.

* ProtocolRegistry.
* HandlerRegistry. 
* BehaviourRegistry.
* TaskRegistry.


## Director

!!! TODO 

## Orchestrator

!!! TODO 




## File structure

The file structure of an agent is fixed.

The top level directory has the agent's name. Below is a `yaml` configuration file, then directories containing the connections, protocols, and skills, and a security certification file.

The developer can create new directories where necessary but the core structure must remain the same.

The CLI tool provides a way to scaffold out the required directory structure for new agents. See the instructions for that <a href="../scaffolding/" target=_blank>here</a>.

``` bash
agentName/
  agent.yml       YAML configuration of the agent
  connections/    Directory containing all the supported connections
    connection1/  First connection
    ...           ...
    connectionN/  nth connection
  protocols/      Directory containing all supported protocols
    protocol1/    First protocol
    ...           ...
    protocolK/    kth protocol 
  skills/         Directory containing all the skill components
    skill1/       First skill
    ...           ...
    skillN/       nth skill
```

<br />

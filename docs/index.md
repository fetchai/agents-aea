# AEA - Autonomous Economic Agent Framework

The AEA framework allows you to quickly assemble autonomous economic agents. Through its modularity AEAs are easily extenable and highly composable.

## Quickstart

`
pip install -i https://test.pypi.org/simple/ aea
`

1. create a new AEA project

`
aea create my_first_agent
`

2. CD into the project folder and add the echo skill to the agent

`
aea add skill echo
`

3. run the agent on a local network

`
aea run
`

## AEA file structure

An agent is structured in a directory with a configuration file, a directory with skills, a directory with protocols, a directory with connections and a main logic file that is used when running aea run.

agentName/                                     | The root of the agent
---------------------------------------------- | -----------------------------------------------------------------
agent.yml                                      | YAML configuration of the agent
connections/                                   | Directory containing all the supported connections
  connection1/                                 | Connection 1
  ...                                          | ...
  connectionN/                                 | Connection N
protocols/                                     | Directory containing all supported protocols
  protocol1/                                   | Protocol 1
  ...                                          | ...
  protocolK/                                   | Protocol K
skills/                                        | Directory containing all the skill components
  skill1/                                      | Skill 1
  ...                                          | ...
  skillN/                                      | Skill L

### AEA Core Components

Envelopes are the core objects which agents use to communicate with each other. An Envelope has four attributes:
- to: defines the destination address
- sender: defines the sender address
- protocol_id: defines the protocol_id
- message: is a bytes field to hold the message in serialized form.

### AEA Protocols

Protocols define how messages are represented and encoded for transport. They also define the rules to which messages have to adhere in a message sequence. For instance, a protocol might have a message of type START and FINISH. Then the rules could prescribe that a message of type FINISH must be preceded by a message of type START.

### AEA Connections

A connection allows the AEA to connect to an external service which has a Python SDK or API. A connection wraps an external SDK or API.

### AEA Skills

A skill can encapsulate any code and ideally delivers economic value to the AEA. Each skill has at most a single Handler and potentially multiple Behaviours and Tasks. The Handler is responsible for dealing with messages of the protocol type for which this skill is registered, as such it encapsulates `reactions`. A Behaviour encapsulates `actions`, that is sequences of interactions with other agents initiated by the AEA. Finally, a Task encapsulates background work which is internal to the AEA.

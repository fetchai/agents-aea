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

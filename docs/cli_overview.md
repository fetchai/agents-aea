# Command Line Interface

The command line interface of the AEA helps you quickly assemble autonomous economic agents.

Command                                        | Description
---------------------------------------------- | -----------------------------------------------------------------
create [name]                                  | Creates a new aea project
fetch [name]                                   | Fetches an aea project
scaffold connection/protocol/skill [name]      | Scaffolds a new connection, protocol or skill project
publish agent/connection/protocol/skill [name] | Publishes agent, connection, protocol or skill project
add connection/protocol/skill [name]           | Adds connection, protocol or skill to agent
remove connection/protocol/skill [name]        | Removes connection, protocol or skill from agent
run {using [connection, ...]}                  | Runs the agent on the Fetch.AI network with the default or specified connections.
deploy {using [connection, ...]}               | Deploys the agent to a server and runs it on the Fetch.AI network with the default or specified connections.
delete [name]                                  | Delete an aea project

# CLI commands


Command  | Description
---------| -----------------------------------------------------------------
`create [name]` | Create a new aea project.
`fetch [name]`   | Fetch an aea project.
`scaffold connection/protocol/skill [name]`  | Scaffold a new connection, protocol, or skill.
`publish agent/connection/protocol/skill [name]` | Publish agent, connection, protocol, or skill.
`add connection/protocol/skill [name]`  | Add connection, protocol, or skill to agent.
`remove connection/protocol/skill [name]` | Remove connection, protocol, or skill from agent.
`run {using [connection, ...]}`  | Run the agent on the Fetch.AI network with default or specified connections.
`-v DEBUG run` | Run with debugging.
`deploy {using [connection, ...]}`  | Deploy the agent to a server and run it on the Fetch.AI network with default or specified connections.
`delete [name]`  | Delete an aea project. See below for disabling a resource.


!!!	Tip
	You can also disable a resource without deleting it by removing the entry from the configuration but leaving the package in the skills namespace.



<br />
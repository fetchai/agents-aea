# CLI commands


Command  | Description
---------| -----------------------------------------------------------------
`create [name]` | Create a new aea project called `[name]`.
`fetch [name]`   | Fetch an aea project called `[name]`.
`scaffold connection/protocol/skill [name]`  | Scaffold a new connection, protocol, or skill called `[name]`.
`publish agent/connection/protocol/skill [name]` | Publish agent, connection, protocol, or skill called `[name]`.
`add connection/protocol/skill [name]`  | Add connection, protocol, or skill, called `[name]`, to the agent.
`remove connection/protocol/skill [name]` | Remove connection, protocol, or skill, called `[name]`, from agent.
`run {using [connection, ...]}`  | Run the agent on the Fetch.AI network with default or specified connections.
`-v DEBUG run` | Run with debugging.
`deploy {using [connection, ...]}`  | Deploy the agent to a server and run it on the Fetch.AI network with default or specified connections.
`delete [name]`  | Delete an aea project called `[name]`. See below for disabling a resource.


!!!	Tip
	You can also disable a resource without deleting it by removing the entry from the configuration but leaving the package in the skills namespace.



<br />
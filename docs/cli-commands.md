# CLI commands


Command  | Description
---------| -----------------------------------------------------------------
`add connection/protocol/skill [name]`  | Add connection, protocol, or skill, called `[name]`, to the agent.
`create NAME` | Create a new aea project called `[name]`.
`delete NAME`  | Delete an aea project. See below for disabling a resource.
`fetch NAME`   | Fetch an aea project called `[name]`.
`freeze`  | Get all the dependencies needed for the aea project and its components.
`gui`  | Run the GUI.
`generate-key default/fetchai/ethereum/all`  | Generate private keys.
`install [-r <requirements_file>]` | Install the dependencies.
`list protocols/connections/skills` |   List the installed resources.
`remove connection/protocol/skill [name]` | Remove connection, protocol, or skill, called `[name]`, from agent.
`run {using [connection, ...]}`  | Run the agent on the Fetch.ai network with default or specified connections.
`search protocols/connections/skills` | Search for components in the registry.
`scaffold connection/protocol/skill [name]`  | Scaffold a new connection, protocol, or skill called `[name]`.
`-v DEBUG run` | Run with debugging.

<!-- 
Command  | Description
---------| -----------------------------------------------------------------
`create [name]` | Create a new aea project.
`fetch [name]`   | Fetch an aea project.
`scaffold connection/protocol/skill [name]`  | Scaffold a new connection, protocol, or skill.
`publish agent/connection/protocol/skill [name]` | Publish agent, connection, protocol, or skill called `[name]`.
`add connection/protocol/skill [name]`  | Add connection, protocol, or skill to agent.
`remove connection/protocol/skill [name]` | Remove connection, protocol, or skill from agent.
`install [-r <requirements_file>]` | Install the dependencies.
`list protocols/connections/skills` |   List the installed resources.
`search protocols/connections/skills` | Search for components in the registry.
`run {using [connection, ...]}`  | Run the agent on the Fetch.ai network with default or specified connections.
`-v DEBUG run` | Run with debugging.
`deploy {using [connection, ...]}`  | Deploy the agent to a server and run it on the Fetch.ai network with default or specified connections.
`delete [name]`  | Delete an aea project called `[name]`. See below for disabling a resource.

 -->

!!!	Tip
	You can also disable a resource without deleting it by removing the entry from the configuration but leaving the package in the skills namespace.



<br />
# CLI commands

| Command                                     | Description                                                                  |
| ------------------------------------------- | ---------------------------------------------------------------------------- |
| `add connection/protocol/skill [name]`      | Add connection, protocol, or skill, called `[name]`, to the agent.           |
| `create NAME`                               | Create a new aea project called `[name]`.                                    |
| `delete NAME`                               | Delete an aea project. See below for disabling a resource.                   |
| `fetch NAME`                                | Fetch an aea project called `[name]`.                                        |
| `freeze`                                    | Get all the dependencies needed for the aea project and its components.      |
| `gui`                                       | Run the GUI.                                                                 |
| `generate-key default/fetchai/ethereum/all` | Generate private keys.                                                       |
| `install [-r <requirements_file>]`          | Install the dependencies.                                                    |
| `list protocols/connections/skills`         | List the installed resources.                                                |
| `remove connection/protocol/skill [name]`   | Remove connection, protocol, or skill, called `[name]`, from agent.          |
| `run {using [connection, ...]}`             | Run the agent on the Fetch.ai network with default or specified connections. |
| `search protocols/connections/skills`       | Search for components in the registry.                                       |
| `scaffold connection/protocol/skill [name]` | Scaffold a new connection, protocol, or skill called `[name]`.               |
| `-v DEBUG run`                              | Run with debugging.                                                          |

<!--
Command  | Description
---------| -----------------------------------------------------------------
`add connection/protocol/skill [name]`  | Add connection, protocol, or skill, called `[name]`, to the agent.
`create NAME` | Create a new aea project called `[name]`.
`delete NAME`  | Delete an aea project. See below for disabling a resource.
`deploy {using [connection, ...]}`  | Deploy the agent to a server and run it on the Fetch.ai network with default or specified connections.
`fetch NAME`   | Fetch an aea project called `[name]`.
`freeze`  | Get all the dependencies needed for the aea project and its components.
`gui`  | Run the GUI.
`generate-key default/fetchai/ethereum/all`  | Generate private keys.
`install [-r <requirements_file>]` | Install the dependencies.
`list protocols/connections/skills` |   List the installed resources.
`remove connection/protocol/skill [name]` | Remove connection, protocol, or skill, called `[name]`, from agent.
`run {using [connection, ...]}`  | Run the agent on the Fetch.ai network with default or specified connections.
`publish agent/connection/protocol/skill [name]` | Publish agent, connection, protocol, or skill called `[name]`.
`search protocols/connections/skills` | Search for components in the registry.
`scaffold connection/protocol/skill [name]`  | Scaffold a new connection, protocol, or skill called `[name]`.
`-v DEBUG run` | Run with debugging.
 -->

!!!	Tip
	You can also disable a resource without deleting it by removing the entry from the configuration but leaving the package in the skills namespace.

<div class="admonition tip">
  <p class="admonition-title">Tip</p>
  <p>You can also disable a resource without deleting it by removing the entry from the configuration but leaving the package in the skills namespace.</p>
</div>

<br />

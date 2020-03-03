# CLI commands

| Command                                     | Description                                                                  |
| ------------------------------------------- | ---------------------------------------------------------------------------- |
| `add connection/protocol/skill [public_id]` | Add connection, protocol, or skill, with `[public_id]`, to the AEA. `add --registry` to add from remote registry. |
| `add-key fetchai/ethereum file`             | Add a private key from a file.	                                             |
| `create NAME`                               | Create a new aea project called `[name]`.                                    |
| `config get [path]`                         | Reads the config specified in `[path]` and prints its target.                |
| `config set [path] [--type TYPE]`           | Sets a new value for the target of the `[path]`. Optionally cast to type.    |
| `delete NAME`                               | Delete an aea project. See below for disabling a resource.                   |
| `fetch PUBLIC_ID`                           | Fetch an aea project with `[public_id]`. `fetch --registry` to fetch from remote registry. |
| `freeze`                                    | Get all the dependencies needed for the aea project and its components.      |
| `gui`                                       | Run the GUI.                                                                 |
| `generate-key fetchai/ethereum/all`         | Generate private keys. The AEA uses a private key to derive the associated public key and address. |
| `generate-wealth fetchai/ethereum`          | Generate wealth for address on test network.                                 |
| `get-address fetchai/ethereum`              | Get the address associated with the private key.                             |
| `get-wealth fetchai/ethereum`               | Get the wealth associated with the private key.                              |
| `install [-r <requirements_file>]`          | Install the dependencies. (With `--install-deps` to install dependencies.)   |
| `init`                                      | Initialize your AEA configurations. (With `--author` to define author.)      |
| `launch [path_to_agent_project]...`         | Launch many agents.                                                          |
| `list protocols/connections/skills`         | List the installed resources.                                                |
| `login USERNAME [--password password]`      | Login to a registry account with credentials.                                |
| `publish`                                   | Publish the AEA to registry. Needs to be executed from an AEA project.`publish --registry` to publish to remote registry. |
| `push connection/protocol/skill [public_id]`| Push connection, protocol, or skill with `[public_id]` to registry.	`push --registry` to push to remote registry. |
| `remove connection/protocol/skill [name]`   | Remove connection, protocol, or skill, called `[name]`, from AEA.            |
| `run {using [connections, ...]}`            | Run the AEA on the Fetch.ai network with default or specified connections.   |
| `search protocols/connections/skills`       | Search for components in the registry. `search --registry protocols/connections/skills [--query searching_query]` to search in remote registry. |
| `scaffold connection/protocol/skill [name]` | Scaffold a new connection, protocol, or skill called `[name]`.               |
| `-v DEBUG run`                              | Run with debugging.                                                          |

<!--
Command  | Description
---------| -----------------------------------------------------------------
`deploy {using [connection, ...]}`  | Deploy the AEA to a server and run it on the Fetch.ai network with default or specified connections.
 -->

<div class="admonition tip">
  <p class="admonition-title">Tip</p>
  <p>You can also disable a resource without deleting it by removing the entry from the configuration but leaving the package in the skills namespace.</p>
</div>

<br />

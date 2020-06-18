# CLI commands

| Command                                     | Description                                                                  |
| ------------------------------------------- | ---------------------------------------------------------------------------- |
| `add [package_type] [public_id]`            | Add a `package_type` connection, contract, protocol, or skill, with `[public_id]`, to the AEA. `add --local` to add from local `packages` directory. |
| `add-key [ledger_id] file`                  | Add a private key from a file for `ledger_id`.	                             |
| `create [name]`                             | Create a new aea project called `name`.                                    |
| `config get [path]`                         | Reads the config specified in `path` and prints its target.                |
| `config set [path] [--type TYPE]`           | Sets a new value for the target of the `path`. Optionally cast to type.    |
| `delete [name]`                             | Delete an aea project. See below for disabling a resource.                   |
| `eject [package_type] [public_id]`          | Move a package of `package_type` and `package_id` from vendor to project working directory. |
| `fetch [public_id]`                         | Fetch an aea project with `public_id`. `fetch --local` to fetch from local `packages` directory. |
| `fingerprint [package_type] [public_id]`    | Fingerprint connection, contract, protocol, or skill, with `public_id`.    |
| `freeze`                                    | Get all the dependencies needed for the aea project and its components.      |
| `gui`                                       | Run the GUI.                                                                 |
| `generate protocol [protocol_spec_path]`    | Generate a protocol from the specification.                                  |
| `generate-key [ledger_id]`                  | Generate private keys. The AEA uses a private key to derive the associated public key and address. |
| `generate-wealth [ledger_id]`               | Generate wealth for address on test network.                                 |
| `get-address [ledger_id]`                   | Get the address associated with the private key.                             |
| `get-wealth [ledger_id]`                    | Get the wealth associated with the private key.                              |
| `install [-r <requirements_file>]`          | Install the dependencies. (With `--install-deps` to install dependencies.)   |
| `init`                                      | Initialize your AEA configurations. (With `--author` to define author.)      |
| `interact`                                  | Interact with a running AEA via the stub connection.                         |
| `launch [path_to_agent_project]...`         | Launch many agents at the same time.                                         |
| `list [package_type]`                       | List the installed resources.                                                |
| `login USERNAME [--password password]`      | Login to a registry account with credentials.                                |
| `logout`                                    | Logout from registry account.                                                |
| `publish`                                   | Publish the AEA to registry. Needs to be executed from an AEA project.`publish --local` to publish to local `packages` directory. |
| `push [protocol_type] [public_id]`          | Push connection, protocol, or skill with `public_id` to registry.	`push --local` to push to local `packages` directory. |
| `remove [protocol_type] [name]`             | Remove connection, protocol, or skill, called `name`, from AEA.            |
| `run {using [connections, ...]}`            | Run the AEA on the Fetch.ai network with default or specified connections.   |
| `search [protocol_type]`                    | Search for components in the registry. `search --local [protocol_type] [--query searching_query]` to search in local `packages` directory. |
| `scaffold [protocol_type] [name]`           | Scaffold a new connection, protocol, or skill called `name`.               |
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

<div class="admonition tip">
  <p class="admonition-title">Tip</p>
  <p>You can skip the consistency checks on the AEA project by using the flag `--skip-consistency-check`. E.g. `aea --skip-consistency-check run` will bypass the fingerprint checks.</p>
</div>

<br />

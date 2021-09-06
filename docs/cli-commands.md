# CLI commands

| Command                                     | Description                                                                  |
| ------------------------------------------- | ---------------------------------------------------------------------------- |
| `add [package_type] [public_id]`            | Add a `package_type` connection, contract, protocol, or skill, with `[public_id]`, to the AEA. `add --local` to add from local `packages` directory. |
| `add-key [ledger_id] file [--connection]`   | Add a private key from a file for `ledger_id`.	                             |
| `build`                                     | Build the agent and its components.                      |
| `config get [path]`                         | Reads the configuration specified in `path` and prints its target.                |
| `config set [path] [--type TYPE]`           | Sets a new value for the target of the `path`. Optionally cast to type.    |
| `create [name]`                             | Create a new AEA project called `name`.                                    |
| `delete [name]`                             | Delete an AEA project. See below for disabling a resource.                   |
| `eject [package_type] [public_id]`          | Move a package of `package_type` and `package_id` from vendor to project working directory. |
| `fetch [public_id]`                         | Fetch an AEA project with `public_id`. `fetch --local` to fetch from local `packages` directory. |
| `fingerprint [package_type] [public_id]`    | Fingerprint connection, contract, protocol, or skill, with `public_id`.    |
| `freeze`                                    | Get all the dependencies needed for the AEA project and its components.      |
| `generate protocol [protocol_spec_path]`    | Generate a protocol from the specification.                                  |
| `generate-key [ledger_id]`                  | Generate private keys. The AEA uses a private key to derive the associated public key and address. |
| `generate-wealth [ledger_id]`               | Generate wealth for address on test network.                                 |
| `get-address [ledger_id]`                   | Get the address associated with the private key.                             |
| `get-multiaddress [ledger_id]...`           | Get the multiaddress associated with a private key or connection.            |
| `get-public-key [ledger_id]...`             | Get the public key associated with a private key of the agent.               |
| `get-wealth [ledger_id]`                    | Get the wealth associated with the private key.                              |
| `init`                                      | Initialize your AEA configurations. (With `--author` to define author.)      |
| `install [-r <requirements_file>]`          | Install the dependencies. (With `--install-deps` to install dependencies.)   |
| `interact`                                  | Interact with a running AEA via the stub connection.                         |
| `ipfs`                                      | IPFS Commands                                                                |
| `issue-certificates`                        | Issue the connection certificates.                                           |
| `launch [path_to_agent_project]...`         | Launch many agents at the same time.                                         |
| `list [package_type]`                       | List the installed resources.                                                |
| `local-registry-sync`                       | Upgrade the local package registry.                                          |
| `login USERNAME [--password password]`      | Login to a registry account with credentials.                                |
| `logout`                                    | Logout from registry account.                                                |
| `publish`                                   | Publish the AEA to registry. Needs to be executed from an AEA project.`publish --local` to publish to local `packages` directory. |
| `push [package_type] [public_id]`           | Push connection, protocol, or skill with `public_id` to registry.	`push --local` to push to local `packages` directory. |
| `register`                                  | Create a new registry account.
| `remove [package_type] [name]`              | Remove connection, protocol, or skill, called `name`, from AEA.            |
| `remove-key [ledger_id] [name]`             | Remove a private key registered with id `ledger_id`.	                             |
| `reset_password EMAIL`                      | Reset the password of the registry account.	                                 |
| `run {using [connections, ...]}`            | Run the AEA on the Fetch.ai network with default or specified connections.   |
| `scaffold [package_type] [name]`            | Scaffold a new connection, protocol, or skill called `name`.               |
| `search [package_type]`                     | Search for components in the registry. `search --local [package_type] [--query searching_query]` to search in local `packages` directory. |
| `transfer [type] [address] [amount]`        | Transfer wealth associated with a private key of the agent to another account. |
| `upgrade [package_type] [public_id]`        | Upgrade the packages of the agent.                               |
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
  <p>You can skip the consistency checks on the AEA project by using the flag <code>--skip-consistency-check</code>. E.g. <code>aea --skip-consistency-check run</code> will bypass the fingerprint checks.</p>
</div>

<br />

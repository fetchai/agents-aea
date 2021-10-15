This page provides some tips on how to upgrade AEA projects between different versions of the AEA framework. For full release notes check the <a href="https://github.com/fetchai/agents-aea/tags" target="_blank">AEA repo</a>.

The primary tool for upgrading AEA projects is the `aea upgrade` command in the <a href="../cli-commands/">CLI</a>.

Below we describe the additional manual steps required to upgrade between different versions:

## `v1.0.2` to `v1.1.0`

No backwards incompatible changes.

We advise everyone to upgrade their `fetchai` packages and plugins to get the latest fixes.

## `v1.0.1` to `v1.0.2`

No backwards incompatible changes.

We advise everyone to upgrade their `fetchai` packages and plugins to get the latest fixes.

## `v1.0.0` to `v1.0.1`

No backwards incompatible changes.

We advise everyone to upgrade their `fetchai` packages to get the latest fixes.

## `v1.0.0rc2` to `v1.0.0`

No backwards incompatible changes to component development.

We advise everyone to upgrade to `v1` as soon as possible. When upgrading from versions below `v1.0.0rc1` first upgrade to the first release candidate, then to `v1`.

## `v1.0.0rc1` to `v1.0.0rc2`

No backwards incompatible changes to component development.

Various configuration changes introduced in `v1.0.0rc1` are now enforced strictly.

## `v0.11.1` to `v1.0.0rc1`

No backwards incompatible changes to component development.

The `aea-config.yaml` now requires the field `required_ledgers` which must specify all ledgers for which private keys are required to run the agent. Please add it to your project.

The `registry_path` field has been removed from the `aea-config.yaml`. Please remove it from your project.

All packages provided by author `fetchai` must be upgraded.

## `v0.11.0` to `v0.11.1`

No backwards incompatible changes.

## `v0.10.1` to `v0.11.0`

Take special care when upgrading to `v0.11.0`. We introduced several breaking changes in preparation for `v1`!

### CLI GUI

We removed the CLI GUI. It was not used by anyone as far as we know and needs to be significantly improved. Soon we will release the AEA Manager App to make up for this.

### Message routing

Routing has been completely revised and simplified. The new message routing logic is described <a href="../message-routing/">here</a>.

When upgrading take the following steps:

- For agent-to-agent communication: ensure the default routing and default connection are correctly defined and that the dialogues used specify the agent's address as the `self_address`. This is most likely already the case. Only in some edge cases will you need to use an `EnvelopeContext` to target a connection different from the one specified in the `default_routing` map.

- For component-to-component communication: there is now only one single way to route component to component (skill to skill, skill to connection, connection to skill) messages, this is by specifying the component id in string form in the `sender`/`to` field. The `EnvelopeContext` can no longer be used, messages are routed based on their target (`to` field). Ensure that dialogues in skills set the `skill_id` as the `self_address` (in connections they need to set the `connection_id`).

### Agent configuration and ledger plugins

Agent configuration files have a new optional field, `dependencies`,  analogous to `dependencies` field in other AEA packages. The default value is the empty object `{}`. The field will be made mandatory in the next release.

Crypto modules have been extracted and released as independent plug-ins, released on PyPI. In particular:

- Fetch.ai crypto classes have been released in the `aea-ledger-fetchai` package;
- Ethereum crypto classes have been released in the `aea-ledger-ethereum` package;
- Cosmos crypto classes have been released in the `aea-ledger-cosmos` package.

If an AEA project, or an AEA package, makes use of crypto functionalities, it will be needed to add the above packages as PyPI dependencies with version specifiers ranging from the latest minor and the latest minor + 1 (excluded). E.g. if the latest version if `0.1.0`, the version specifier should be `<0.2.0,>=0.1.0`:
```yaml
dependencies:
  aea-ledger-cosmos:
    version: <2.0.0,>=1.0.0
  aea-ledger-ethereum:
    version: <2.0.0,>=1.0.0
  aea-ledger-fetchai:
    version: <2.0.0,>=1.0.0
```
The version specifier sets are important, as these plug-ins, at version `0.1.0`, depend on a specific range of the `aea` package.

Then, running `aea install` inside the AEA project should install them in the current Python environment.

For more, read the <a href="../ledger-integration">guide on ledger plugins</a>.

## `v0.10.0` to `v0.10.1`

No backwards incompatible changes for skill and connection development.

## `v0.9.2` to `v0.10.0`

Skill development sees no backward incompatible changes. 

Connection development requires updating the keyword arguments of the constructor: the new `data_dir` argument must be defined.

Protocol specifications now need to contain a `protocol_specification_id` in addition to the public id. The `protocol_specification_id` is used for identifying Envelopes during transport. By being able to set the id independently of the protocol id, backwards compatibility in the specification (and therefore wire format) can be maintained even when the Python implementation changes.

Please update to the latest packages by running `aea upgrade` and then re-generating your own protocols.

## `v0.9.1` to `v0.9.2`

No backwards incompatible changes for skill and connection development.

## `v0.9.0` to `v0.9.1`

No backwards incompatible changes for skill and connection development.

## `v0.8.0` to `v0.9.0`

This release introduces <a href="../por">proof of representation</a> in the ACN. You will need to upgrade to the latest `fetchai/p2p_libp2p` or `fetchai/p2p_libp2p_client` connection and then use two key pairs, one for your AEA's decision maker and one for the connection.

Please update to the latest packages by running `aea upgrade`.

## `v0.7.5` to `v0.8.0`

Minimal backwards incompatible changes for skill and connection development:

- The semantics of the `<`, `<=`, `>` and `>=` relations in `ConstraintTypes` are simplified.
- Protocols now need to correctly define terminal states. Regenerate your protocol to identify if your protocol's dialogue rules are valid.

Please update to the latest packages by running `aea upgrade`.

## `v0.7.4` to `v0.7.5`

No backwards incompatible changes for skill and connection development.

## `v0.7.3` to `v0.7.4`

No backwards incompatible changes for skill and connection development.

## `v0.7.2` to `v0.7.3`

No backwards incompatible changes for skill and connection development.

## `v0.7.1` to `v0.7.2`

No backwards incompatible changes for skill and connection development.

## `v0.7.0` to `v0.7.1`

To improve performance, in particular optimize memory usage, we refactored the `Message` and `Dialogue` classes. This means all protocols need to be bumped to the latest version or regenerated using the `aea generate protocol` command in the <a href="../cli-commands/">CLI</a>.

## `v0.6.3` to `v0.7.0`

Multiple breaking changes require action in this order:

- Custom configuration overrides in `aea-config.yaml` are now identified via `public_id` rather than `author`, `name` and `version` individually. Please replace the three fields with the equivalent `public_id`.

- Run `aea upgrade` command to upgrade your project's dependencies. Note, you still do have to manually update the public ids under `default_routing` and `default_connection` in `aea-config.yaml` as well as the public ids in the non-vendor packages.

- Previously, connection `fetchai/stub`, skill `fetchai/error` and protocols `fetchai/default`, `fetchai/signing` and `fetchai/state_update` where part of the AEA distribution. Now they need to be fetched from registry. If you create a new project with `aea create` then this happens automatically. For existing projects, add the dependencies explicitly if not already present. You also must update the import paths as follows:

    - `aea.connections.stub` > `packages.fetchai.connections.stub`
    - `aea.protocols.default` > `packages.fetchai.protocols.default`
    - `aea.protocols.signing` > `packages.fetchai.protocols.signing`
    - `aea.protocols.state_update` > `packages.fetchai.protocols.state_update`
    - `aea.skills.error` > `packages.fetchai.skills.error`

- If you use custom protocols, regenerate them.

- In your own skills' `__init__.py` files add the public id (updating the string as appropriate):

``` python
from aea.configurations.base import PublicId


PUBLIC_ID = PublicId.from_str("author/name:0.1.0")
```
- The `fetchai/http` protocol's `bodyy` field has been renamed to `body`.

- Skills can now specify `connections` as dependencies in the configuration YAML.


## `v0.6.2` to `v0.6.3`

A new `upgrade` command is introduced to upgrade agent projects and components to their latest versions on the registry. To use the command first upgrade the AEA PyPI package to the latest version, then enter your project and run `aea upgrade`. The project's vendor dependencies will be updated where possible.

## `v0.6.1` to `v0.6.2`

No public APIs have been changed.

## `v0.6.0` to `v0.6.1`

The `soef` connection and `oef_search` protocol have backward incompatible changes.

## `v0.5.4` to `v0.6.0`

### `Dialogue` and `Dialogues` API updates

The dialogue and dialogues APIs have changed significantly. The constructor is different for both classes and there are now four primary methods for the developer:

- `Dialogues.create`: this method is used to create a new dialogue and message:
``` python
cfp_msg, fipa_dialogue = fipa_dialogues.create(
    counterparty=opponent_address,
    performative=FipaMessage.Performative.CFP,
    query=query,
)
```
The method will raise if the provided arguments are inconsistent.

- `Dialogues.create_with_message`: this method is used to create a new dialogue from a message:
``` python
fipa_dialogue = fipa_dialogues.create_with_message(
    counterparty=opponent_address,
    initial_message=cfp_msg
)
```
The method will raise if the provided arguments are inconsistent.

- `Dialogues.update`: this method is used to handle messages passed by the framework:
``` python
fipa_dialogue = fipa_dialogues.update(
    message=cfp_msg
)
```
The method will return a valid dialogue if it is a valid message, otherwise it will return `None`.

- `Dialogue.reply`: this method is used to reply within a dialogue:
``` python
proposal_msg = fipa_dialogue.reply(
    performative=FipaMessage.Performative.PROPOSE,
    target_message=cfp_msg,
    proposal=proposal,
)
```
The method will raise if the provided arguments are inconsistent.

The new methods significantly reduce the lines of code needed to maintain a dialogue. They also make it easier for the developer to construct valid dialogues and messages.

### `FetchAICrypto` - default crypto

The `FetchAICrypto` has been upgraded to the default crypto. Update your `default_ledger` to `fetchai`.

### Private key file naming

The private key files are now consistently named with the `ledger_id` followed by `_private_key.txt` (e.g. `fetchai_private_key.txt`). Rename your existing files to match this pattern.

### Type in package YAML

The package YAML files now contain a type field. This must be added for the loading mechanism to work properly.

### Moved address type

The address type has moved to `aea.common`. The import paths must be updated.

## `v0.5.3` to `v0.5.4`

The contract base class was slightly modified. If you have implemented your own contract package you need to update it accordingly.

The dialogue reference nonce is now randomly generated. This can result in previously working but buggy implementations (which relied on the order of dialogue reference nonces) to now fail.

## `v0.5.2` to `v0.5.3`

Connection states and logger usage in connections where updated. If you have implemented your own connection package you need to update it accordingly.

Additional dialogue consistency checks where enabled. This can result in previously working but buggy implementations to now fail.

## `v0.5.1` to `0.5.2`

No public APIs have been changed.

## `v0.5.0` to `0.5.1`

No public APIs have been changed.

## `v0.4.1` to `0.5.0`

A number of breaking changes where introduced which make backwards compatibility of skills rare.

- Ledger APIs <a href="../api/crypto/ledger_apis#ledger-apis-objects">`LedgerApis`</a> have been removed from the AEA constructor and skill context. `LedgerApis` are now exposed in the `LedgerConnection` (`fetchai/ledger`). To communicate with the `LedgerApis` use the `fetchai/ledger_api` protocol. This allows for more flexibility (anyone can add another `LedgerAPI` to the registry and execute it with the connection) and removes dependencies from the core framework.
- Skills can now depend on other skills. As a result, skills have a new required configuration field in `skill.yaml` files, by default empty: `skills: []`.

## `v0.4.0` to `v0.4.1`

There are no upgrade requirements if you use the CLI based approach to AEA development.

Connections are now added via <a href="../api/registries/resources#resources-objects">`Resources`</a> to the AEA, not the AEA constructor directly. For programmatic usage remove the list of connections from the AEA constructor and instead add the connections to resources.

## `v0.3.3` to `v0.4.0`

<ul>
<li> Message sending in the skills has been updated. In the past you had to construct messages, then serialize them and place them in an envelope:

``` python
cfp_msg = FipaMessage(...)
self.context.outbox.put_message(
    to=opponent_addr,
    sender=self.context.agent_address,
    protocol_id=FipaMessage.protocol_id,
    message=FipaSerializer().encode(cfp_msg),
)
# or
cfp_msg = FipaMessage(...)
envelope = Envelope(
    to=opponent_addr,
    sender=self.context.agent_address,
    protocol_id=FipaMessage.protocol_id,
    message=FipaSerializer().encode(cfp_msg),
)
self.context.outbox.put(envelope)
```

Now this has been simplified to:
``` python
cfp_msg = FipaMessage(...)
cfp_msg.counterparty = opponent_addr
self.context.outbox.put_message(message=cfp_msg)
```

You must update your skills as the old implementation is no longer supported.
</li>
<li> Connection constructors have been simplified. In the past you had to implement both the `__init__` as well as the `from_config` methods of a Connection. Now you only have to implement the `__init__` method which by default at load time now receives the following keyword arguments: `configuration: ConnectionConfig, identity: Identity, crypto_store: CryptoStore`. See for example in the scaffold connection:

``` python
class MyScaffoldConnection(Connection):
    """Proxy to the functionality of the SDK or API."""

    connection_id = PublicId.from_str("fetchai/scaffold:0.1.0")

    def __init__(
        self,
        configuration: ConnectionConfig,
        identity: Identity,
        crypto_store: CryptoStore,
    ):
        """
        Initialize a connection to an SDK or API.

        :param configuration: the connection configuration.
        :param crypto_store: object to access the connection crypto objects.
        :param identity: the identity object.
        """
        super().__init__(
            configuration=configuration, crypto_store=crypto_store, identity=identity
        )
```

As a result of this feature, you are now able to pass key-pairs to your connections via the `CryptoStore`.

You must update your connections as the old implementation is no longer supported.
</li>
</ul>

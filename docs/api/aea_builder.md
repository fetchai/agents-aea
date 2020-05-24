<a name=".aea.aea_builder"></a>
## aea.aea`_`builder

This module contains utilities for building an AEA.

<a name=".aea.aea_builder.AEABuilder"></a>
### AEABuilder

```python
class AEABuilder()
```

This class helps to build an AEA.

It follows the fluent interface. Every method of the builder
returns the instance of the builder itself.

<a name=".aea.aea_builder.AEABuilder.__init__"></a>
#### `__`init`__`

```python
 | __init__(with_default_packages: bool = True)
```

Initialize the builder.

**Arguments**:

- `with_default_packages`: add the default packages.

<a name=".aea.aea_builder.AEABuilder.set_timeout"></a>
#### set`_`timeout

```python
 | set_timeout(timeout: Optional[float]) -> "AEABuilder"
```

Set agent loop idle timeout in seconds.

**Arguments**:

- `timeout`: timeout in seconds

**Returns**:

self

<a name=".aea.aea_builder.AEABuilder.set_execution_timeout"></a>
#### set`_`execution`_`timeout

```python
 | set_execution_timeout(execution_timeout: Optional[float]) -> "AEABuilder"
```

Set agent execution timeout in seconds.

**Arguments**:

- `execution_timeout`: execution_timeout in seconds

**Returns**:

self

<a name=".aea.aea_builder.AEABuilder.set_max_reactions"></a>
#### set`_`max`_`reactions

```python
 | set_max_reactions(max_reactions: Optional[int]) -> "AEABuilder"
```

Set agent max reaction in one react.

**Arguments**:

- `max_reactions`: int

**Returns**:

self

<a name=".aea.aea_builder.AEABuilder.set_decision_maker_handler"></a>
#### set`_`decision`_`maker`_`handler

```python
 | set_decision_maker_handler(decision_maker_handler_dotted_path: str, file_path: Path) -> "AEABuilder"
```

Set decision maker handler class.

**Arguments**:

- `decision_maker_handler_dotted_path`: the dotted path to the decision maker handler
- `file_path`: the file path to the file which contains the decision maker handler

**Returns**:

self

<a name=".aea.aea_builder.AEABuilder.set_skill_exception_policy"></a>
#### set`_`skill`_`exception`_`policy

```python
 | set_skill_exception_policy(skill_exception_policy: Optional[ExceptionPolicyEnum]) -> "AEABuilder"
```

Set skill exception policy.

**Arguments**:

- `skill_exception_policy`: the policy

**Returns**:

self

<a name=".aea.aea_builder.AEABuilder.set_default_routing"></a>
#### set`_`default`_`routing

```python
 | set_default_routing(default_routing: Dict[PublicId, PublicId]) -> "AEABuilder"
```

Set default routing.

This is a map from public ids (protocols) to public ids (connections).

**Arguments**:

- `default_routing`: the default routing mapping

**Returns**:

self

<a name=".aea.aea_builder.AEABuilder.set_loop_mode"></a>
#### set`_`loop`_`mode

```python
 | set_loop_mode(loop_mode: Optional[str]) -> "AEABuilder"
```

Set the loop mode.

**Arguments**:

- `loop_mode`: the agent loop mode

**Returns**:

self

<a name=".aea.aea_builder.AEABuilder.set_name"></a>
#### set`_`name

```python
 | set_name(name: str) -> "AEABuilder"
```

Set the name of the agent.

**Arguments**:

- `name`: the name of the agent.

**Returns**:

the AEABuilder

<a name=".aea.aea_builder.AEABuilder.set_default_connection"></a>
#### set`_`default`_`connection

```python
 | set_default_connection(public_id: PublicId) -> "AEABuilder"
```

Set the default connection.

**Arguments**:

- `public_id`: the public id of the default connection package.

**Returns**:

the AEABuilder

<a name=".aea.aea_builder.AEABuilder.add_private_key"></a>
#### add`_`private`_`key

```python
 | add_private_key(identifier: str, private_key_path: PathLike) -> "AEABuilder"
```

Add a private key path.

**Arguments**:

- `identifier`: the identifier for that private key path.
- `private_key_path`: path to the private key file.

**Returns**:

the AEABuilder

<a name=".aea.aea_builder.AEABuilder.remove_private_key"></a>
#### remove`_`private`_`key

```python
 | remove_private_key(identifier: str) -> "AEABuilder"
```

Remove a private key path by identifier, if present.

**Arguments**:

- `identifier`: the identifier of the private key.

**Returns**:

the AEABuilder

<a name=".aea.aea_builder.AEABuilder.private_key_paths"></a>
#### private`_`key`_`paths

```python
 | @property
 | private_key_paths() -> Dict[str, str]
```

Get the private key paths.

<a name=".aea.aea_builder.AEABuilder.add_ledger_api_config"></a>
#### add`_`ledger`_`api`_`config

```python
 | add_ledger_api_config(identifier: str, config: Dict) -> "AEABuilder"
```

Add a configuration for a ledger API to be supported by the agent.

**Arguments**:

- `identifier`: the identifier of the ledger api
- `config`: the configuration of the ledger api

**Returns**:

the AEABuilder

<a name=".aea.aea_builder.AEABuilder.remove_ledger_api_config"></a>
#### remove`_`ledger`_`api`_`config

```python
 | remove_ledger_api_config(identifier: str) -> "AEABuilder"
```

Remove a ledger API configuration.

**Arguments**:

- `identifier`: the identifier of the ledger api

**Returns**:

the AEABuilder

<a name=".aea.aea_builder.AEABuilder.ledger_apis_config"></a>
#### ledger`_`apis`_`config

```python
 | @property
 | ledger_apis_config() -> Dict[str, Dict[str, Union[str, int]]]
```

Get the ledger api configurations.

<a name=".aea.aea_builder.AEABuilder.set_default_ledger"></a>
#### set`_`default`_`ledger

```python
 | set_default_ledger(identifier: str) -> "AEABuilder"
```

Set a default ledger API to use.

**Arguments**:

- `identifier`: the identifier of the ledger api

**Returns**:

the AEABuilder

<a name=".aea.aea_builder.AEABuilder.add_component"></a>
#### add`_`component

```python
 | add_component(component_type: ComponentType, directory: PathLike, skip_consistency_check: bool = False) -> "AEABuilder"
```

Add a component, given its type and the directory.

**Arguments**:

- `component_type`: the component type.
- `directory`: the directory path.
- `skip_consistency_check`: if True, the consistency check are skipped.

**Raises**:

- `AEAException`: if a component is already registered with the same component id.
| or if there's a missing dependency.

**Returns**:

the AEABuilder

<a name=".aea.aea_builder.AEABuilder.add_component_instance"></a>
#### add`_`component`_`instance

```python
 | add_component_instance(component: Component) -> "AEABuilder"
```

Add already initialized component object to resources or connections.

Please, pay attention, all dependencies have to be already loaded.

:params component: Component instance already initialized.

<a name=".aea.aea_builder.AEABuilder.set_context_namespace"></a>
#### set`_`context`_`namespace

```python
 | set_context_namespace(context_namespace: Dict[str, Any]) -> "AEABuilder"
```

Set the context namespace.

<a name=".aea.aea_builder.AEABuilder.remove_component"></a>
#### remove`_`component

```python
 | remove_component(component_id: ComponentId) -> "AEABuilder"
```

Remove a component.

**Arguments**:

- `component_id`: the public id of the component.

**Returns**:

the AEABuilder

<a name=".aea.aea_builder.AEABuilder.add_protocol"></a>
#### add`_`protocol

```python
 | add_protocol(directory: PathLike) -> "AEABuilder"
```

Add a protocol to the agent.

**Arguments**:

- `directory`: the path to the protocol directory

**Returns**:

the AEABuilder

<a name=".aea.aea_builder.AEABuilder.remove_protocol"></a>
#### remove`_`protocol

```python
 | remove_protocol(public_id: PublicId) -> "AEABuilder"
```

Remove protocol.

**Arguments**:

- `public_id`: the public id of the protocol

**Returns**:

the AEABuilder

<a name=".aea.aea_builder.AEABuilder.add_connection"></a>
#### add`_`connection

```python
 | add_connection(directory: PathLike) -> "AEABuilder"
```

Add a connection to the agent.

**Arguments**:

- `directory`: the path to the connection directory

**Returns**:

the AEABuilder

<a name=".aea.aea_builder.AEABuilder.remove_connection"></a>
#### remove`_`connection

```python
 | remove_connection(public_id: PublicId) -> "AEABuilder"
```

Remove a connection.

**Arguments**:

- `public_id`: the public id of the connection

**Returns**:

the AEABuilder

<a name=".aea.aea_builder.AEABuilder.add_skill"></a>
#### add`_`skill

```python
 | add_skill(directory: PathLike) -> "AEABuilder"
```

Add a skill to the agent.

**Arguments**:

- `directory`: the path to the skill directory

**Returns**:

the AEABuilder

<a name=".aea.aea_builder.AEABuilder.remove_skill"></a>
#### remove`_`skill

```python
 | remove_skill(public_id: PublicId) -> "AEABuilder"
```

Remove protocol.

**Arguments**:

- `public_id`: the public id of the skill

**Returns**:

the AEABuilder

<a name=".aea.aea_builder.AEABuilder.add_contract"></a>
#### add`_`contract

```python
 | add_contract(directory: PathLike) -> "AEABuilder"
```

Add a contract to the agent.

**Arguments**:

- `directory`: the path to the contract directory

**Returns**:

the AEABuilder

<a name=".aea.aea_builder.AEABuilder.remove_contract"></a>
#### remove`_`contract

```python
 | remove_contract(public_id: PublicId) -> "AEABuilder"
```

Remove protocol.

**Arguments**:

- `public_id`: the public id of the contract

**Returns**:

the AEABuilder

<a name=".aea.aea_builder.AEABuilder.build"></a>
#### build

```python
 | build(connection_ids: Optional[Collection[PublicId]] = None, ledger_apis: Optional[LedgerApis] = None) -> AEA
```

Build the AEA.

**Arguments**:

- `connection_ids`: select only these connections to run the AEA.
- `ledger_apis`: the api ledger that we want to use.

**Returns**:

the AEA object.

<a name=".aea.aea_builder.AEABuilder.from_aea_project"></a>
#### from`_`aea`_`project

```python
 | @classmethod
 | from_aea_project(cls, aea_project_path: PathLike, skip_consistency_check: bool = False) -> "AEABuilder"
```

Construct the builder from an AEA project.

- load agent configuration file
- set name and default configurations
- load private keys
- load ledger API configurations
- set default ledger
- load every component

**Arguments**:

- `aea_project_path`: path to the AEA project.
- `skip_consistency_check`: if True, the consistency check are skipped.

**Returns**:

an AEABuilder.


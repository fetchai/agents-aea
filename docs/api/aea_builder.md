<a name=".aea.aea_builder"></a>
## aea.aea`_`builder

This module contains utilities for building an AEA.

<a name=".aea.aea_builder._DependenciesManager.__init__"></a>
#### `__`init`__`

```python
 | __init__()
```

Initialize the dependency graph.

<a name=".aea.aea_builder._DependenciesManager.all_dependencies"></a>
#### all`_`dependencies

```python
 | @property
 | all_dependencies() -> Set[ComponentId]
```

Get all dependencies.

<a name=".aea.aea_builder._DependenciesManager.dependencies_highest_version"></a>
#### dependencies`_`highest`_`version

```python
 | @property
 | dependencies_highest_version() -> Set[ComponentId]
```

Get the dependencies with highest version.

<a name=".aea.aea_builder._DependenciesManager.protocols"></a>
#### protocols

```python
 | @property
 | protocols() -> Dict[ComponentId, Protocol]
```

Get the protocols.

<a name=".aea.aea_builder._DependenciesManager.connections"></a>
#### connections

```python
 | @property
 | connections() -> Dict[ComponentId, Connection]
```

Get the connections.

<a name=".aea.aea_builder._DependenciesManager.skills"></a>
#### skills

```python
 | @property
 | skills() -> Dict[ComponentId, Skill]
```

Get the skills.

<a name=".aea.aea_builder._DependenciesManager.contracts"></a>
#### contracts

```python
 | @property
 | contracts() -> Dict[ComponentId, Any]
```

Get the contracts.

<a name=".aea.aea_builder._DependenciesManager.add_component"></a>
#### add`_`component

```python
 | add_component(component: Component) -> None
```

Add a component to the dependency manager..

**Arguments**:

- `component`: the component to add.

**Returns**:

None

<a name=".aea.aea_builder._DependenciesManager.remove_component"></a>
#### remove`_`component

```python
 | remove_component(component_id: ComponentId)
```

Remove a component.

:return None

**Raises**:

- `ValueError`: if some component depends on this package.

<a name=".aea.aea_builder._DependenciesManager.check_package_dependencies"></a>
#### check`_`package`_`dependencies

```python
 | check_package_dependencies(component_configuration: ComponentConfiguration) -> bool
```

Check that we have all the dependencies needed to the package.

return: True if all the dependencies are covered, False otherwise.

<a name=".aea.aea_builder._DependenciesManager.pypi_dependencies"></a>
#### pypi`_`dependencies

```python
 | @property
 | pypi_dependencies() -> Dependencies
```

Get all the PyPI dependencies.

<a name=".aea.aea_builder._DependenciesManager.load_dependencies"></a>
#### load`_`dependencies

```python
 | @contextmanager
 | load_dependencies()
```

Load dependencies of a component, so its modules can be loaded.

**Returns**:

None

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

<a name=".aea.aea_builder.AEABuilder.add_default_packages"></a>
#### add`_`default`_`packages

```python
 | add_default_packages()
```

Add default packages.

<a name=".aea.aea_builder.AEABuilder.set_name"></a>
#### set`_`name

```python
 | set_name(name: str) -> "AEABuilder"
```

Set the name of the agent.

**Arguments**:

- `name`: the name of the agent.

<a name=".aea.aea_builder.AEABuilder.set_default_connection"></a>
#### set`_`default`_`connection

```python
 | set_default_connection(public_id: PublicId)
```

Set the default connection.

**Arguments**:

- `public_id`: the public id of the default connection package.

**Returns**:

None

<a name=".aea.aea_builder.AEABuilder.add_private_key"></a>
#### add`_`private`_`key

```python
 | add_private_key(identifier: str, private_key_path: PathLike) -> "AEABuilder"
```

Add a private key path.

**Arguments**:

- `identifier`: the identifier for that private key path.
- `private_key_path`: path to the private key file.

<a name=".aea.aea_builder.AEABuilder.remove_private_key"></a>
#### remove`_`private`_`key

```python
 | remove_private_key(identifier: str) -> "AEABuilder"
```

Remove a private key path by identifier, if present.

**Arguments**:

- `identifier`: the identifier of the private key.

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
 | add_ledger_api_config(identifier: str, config: Dict)
```

Add a configuration for a ledger API to be supported by the agent.

<a name=".aea.aea_builder.AEABuilder.remove_ledger_api_config"></a>
#### remove`_`ledger`_`api`_`config

```python
 | remove_ledger_api_config(identifier: str)
```

Remove a ledger API configuration.

<a name=".aea.aea_builder.AEABuilder.ledger_apis_config"></a>
#### ledger`_`apis`_`config

```python
 | @property
 | ledger_apis_config() -> Dict[str, Dict[str, Union[str, int]]]
```

Get the ledger api configurations.

<a name=".aea.aea_builder.AEABuilder.set_default_ledger_api_config"></a>
#### set`_`default`_`ledger`_`api`_`config

```python
 | set_default_ledger_api_config(default: str)
```

Set a default ledger API to use.

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

- `ValueError`: if a component is already registered with the same component id.

<a name=".aea.aea_builder.AEABuilder.remove_component"></a>
#### remove`_`component

```python
 | remove_component(component_id: ComponentId) -> "AEABuilder"
```

Remove a component.

<a name=".aea.aea_builder.AEABuilder.add_protocol"></a>
#### add`_`protocol

```python
 | add_protocol(directory: PathLike) -> "AEABuilder"
```

Add a protocol to the agent.

<a name=".aea.aea_builder.AEABuilder.remove_protocol"></a>
#### remove`_`protocol

```python
 | remove_protocol(public_id: PublicId) -> "AEABuilder"
```

Remove protocol

<a name=".aea.aea_builder.AEABuilder.add_connection"></a>
#### add`_`connection

```python
 | add_connection(directory: PathLike) -> "AEABuilder"
```

Add a protocol to the agent.

<a name=".aea.aea_builder.AEABuilder.remove_connection"></a>
#### remove`_`connection

```python
 | remove_connection(public_id: PublicId) -> "AEABuilder"
```

Remove a connection

<a name=".aea.aea_builder.AEABuilder.add_skill"></a>
#### add`_`skill

```python
 | add_skill(directory: PathLike) -> "AEABuilder"
```

Add a skill to the agent.

<a name=".aea.aea_builder.AEABuilder.remove_skill"></a>
#### remove`_`skill

```python
 | remove_skill(public_id: PublicId) -> "AEABuilder"
```

Remove protocol

<a name=".aea.aea_builder.AEABuilder.add_contract"></a>
#### add`_`contract

```python
 | add_contract(directory: PathLike) -> "AEABuilder"
```

Add a contract to the agent.

<a name=".aea.aea_builder.AEABuilder.remove_contract"></a>
#### remove`_`contract

```python
 | remove_contract(public_id: PublicId) -> "AEABuilder"
```

Remove protocol

<a name=".aea.aea_builder.AEABuilder.build"></a>
#### build

```python
 | build(connection_ids: Optional[Collection[PublicId]] = None) -> AEA
```

Build the AEA.

**Arguments**:

- `connection_ids`: select only these connections.

**Returns**:

the AEA object.

<a name=".aea.aea_builder.AEABuilder.from_aea_project"></a>
#### from`_`aea`_`project

```python
 | @classmethod
 | from_aea_project(cls, aea_project_path: PathLike, skip_consistency_check: bool = False)
```

Construct the builder from an AEA project

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

an AEA agent.


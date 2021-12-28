<a name="aea.aea_builder"></a>
# aea.aea`_`builder

This module contains utilities for building an AEA.

<a name="aea.aea_builder._DependenciesManager"></a>
## `_`DependenciesManager Objects

```python
class _DependenciesManager()
```

Class to manage dependencies of agent packages.

<a name="aea.aea_builder._DependenciesManager.__init__"></a>
#### `__`init`__`

```python
 | __init__() -> None
```

Initialize the dependency graph.

<a name="aea.aea_builder._DependenciesManager.all_dependencies"></a>
#### all`_`dependencies

```python
 | @property
 | all_dependencies() -> Set[ComponentId]
```

Get all dependencies.

<a name="aea.aea_builder._DependenciesManager.dependencies_highest_version"></a>
#### dependencies`_`highest`_`version

```python
 | @property
 | dependencies_highest_version() -> Set[ComponentId]
```

Get the dependencies with highest version.

<a name="aea.aea_builder._DependenciesManager.get_components_by_type"></a>
#### get`_`components`_`by`_`type

```python
 | get_components_by_type(component_type: ComponentType) -> Dict[ComponentId, ComponentConfiguration]
```

Get the components by type.

<a name="aea.aea_builder._DependenciesManager.protocols"></a>
#### protocols

```python
 | @property
 | protocols() -> Dict[ComponentId, ProtocolConfig]
```

Get the protocols.

<a name="aea.aea_builder._DependenciesManager.connections"></a>
#### connections

```python
 | @property
 | connections() -> Dict[ComponentId, ConnectionConfig]
```

Get the connections.

<a name="aea.aea_builder._DependenciesManager.skills"></a>
#### skills

```python
 | @property
 | skills() -> Dict[ComponentId, SkillConfig]
```

Get the skills.

<a name="aea.aea_builder._DependenciesManager.contracts"></a>
#### contracts

```python
 | @property
 | contracts() -> Dict[ComponentId, ContractConfig]
```

Get the contracts.

<a name="aea.aea_builder._DependenciesManager.add_component"></a>
#### add`_`component

```python
 | add_component(configuration: ComponentConfiguration) -> None
```

Add a component to the dependency manager.

**Arguments**:

- `configuration`: the component configuration to add.

<a name="aea.aea_builder._DependenciesManager.remove_component"></a>
#### remove`_`component

```python
 | remove_component(component_id: ComponentId) -> None
```

Remove a component.

**Arguments**:

- `component_id`: the component id

**Raises**:

- `ValueError`: if some component depends on this package.

<a name="aea.aea_builder._DependenciesManager.pypi_dependencies"></a>
#### pypi`_`dependencies

```python
 | @property
 | pypi_dependencies() -> Dependencies
```

Get all the PyPI dependencies.

We currently consider only dependency that have the
default PyPI index url and that specify only the
version field.

**Returns**:

the merged PyPI dependencies

<a name="aea.aea_builder._DependenciesManager.install_dependencies"></a>
#### install`_`dependencies

```python
 | install_dependencies() -> None
```

Install extra dependencies for components.

<a name="aea.aea_builder.AEABuilder"></a>
## AEABuilder Objects

```python
class AEABuilder(WithLogger)
```

This class helps to build an AEA.

It follows the fluent interface. Every method of the builder
returns the instance of the builder itself.

Note: the method 'build()' is guaranteed of being
re-entrant with respect to the 'add_component(path)'
method. That is, you can invoke the building method
many times against the same builder instance, and the
returned agent instance will not share the
components with other agents, e.g.:

builder = AEABuilder()
builder.add_component(...)
...

# first call
my_aea_1 = builder.build()

# following agents will have different components.
my_aea_2 = builder.build()  # all good

However, if you manually loaded some of the components and added
them with the method 'add_component_instance()', then calling build
more than one time is prevented:

builder = AEABuilder()
builder.add_component_instance(...)
...  # other initialization code

# first call
my_aea_1 = builder.build()

# second call to `build()` would raise a Value Error.
# call reset
builder.reset()

# re-add the component and private keys
builder.add_component_instance(...)
... # add private keys

# second call
my_aea_2 = builder.builder()

<a name="aea.aea_builder.AEABuilder.__init__"></a>
#### `__`init`__`

```python
 | __init__(with_default_packages: bool = True, registry_dir: str = DEFAULT_REGISTRY_NAME, build_dir_root: Optional[str] = None) -> None
```

Initialize the builder.

**Arguments**:

- `with_default_packages`: add the default packages.
- `registry_dir`: the registry directory.
- `build_dir_root`: the root of the build directory.

<a name="aea.aea_builder.AEABuilder.reset"></a>
#### reset

```python
 | reset(is_full_reset: bool = False) -> None
```

Reset the builder.

A full reset causes a reset of all data on the builder. A partial reset
only resets:
    - name,
    - private keys, and
    - component instances

**Arguments**:

- `is_full_reset`: whether it is a full reset or not.

<a name="aea.aea_builder.AEABuilder.set_period"></a>
#### set`_`period

```python
 | set_period(period: Optional[float]) -> "AEABuilder"
```

Set agent act period.

**Arguments**:

- `period`: period in seconds

**Returns**:

self

<a name="aea.aea_builder.AEABuilder.set_execution_timeout"></a>
#### set`_`execution`_`timeout

```python
 | set_execution_timeout(execution_timeout: Optional[float]) -> "AEABuilder"
```

Set agent execution timeout in seconds.

**Arguments**:

- `execution_timeout`: execution_timeout in seconds

**Returns**:

self

<a name="aea.aea_builder.AEABuilder.set_max_reactions"></a>
#### set`_`max`_`reactions

```python
 | set_max_reactions(max_reactions: Optional[int]) -> "AEABuilder"
```

Set agent max reaction in one react.

**Arguments**:

- `max_reactions`: int

**Returns**:

self

<a name="aea.aea_builder.AEABuilder.set_decision_maker_handler_details"></a>
#### set`_`decision`_`maker`_`handler`_`details

```python
 | set_decision_maker_handler_details(decision_maker_handler_dotted_path: str, file_path: str, config: Dict[str, Any]) -> "AEABuilder"
```

Set error handler details.

**Arguments**:

- `decision_maker_handler_dotted_path`: the dotted path to the decision maker handler
- `file_path`: the file path to the file which contains the decision maker handler
- `config`: the configuration passed to the decision maker handler on instantiation

**Returns**:

self

<a name="aea.aea_builder.AEABuilder.set_error_handler_details"></a>
#### set`_`error`_`handler`_`details

```python
 | set_error_handler_details(error_handler_dotted_path: str, file_path: str, config: Dict[str, Any]) -> "AEABuilder"
```

Set error handler details.

**Arguments**:

- `error_handler_dotted_path`: the dotted path to the error handler
- `file_path`: the file path to the file which contains the error handler
- `config`: the configuration passed to the error handler on instantiation

**Returns**:

self

<a name="aea.aea_builder.AEABuilder.set_skill_exception_policy"></a>
#### set`_`skill`_`exception`_`policy

```python
 | set_skill_exception_policy(skill_exception_policy: Optional[ExceptionPolicyEnum]) -> "AEABuilder"
```

Set skill exception policy.

**Arguments**:

- `skill_exception_policy`: the policy

**Returns**:

self

<a name="aea.aea_builder.AEABuilder.set_connection_exception_policy"></a>
#### set`_`connection`_`exception`_`policy

```python
 | set_connection_exception_policy(connection_exception_policy: Optional[ExceptionPolicyEnum]) -> "AEABuilder"
```

Set connection exception policy.

**Arguments**:

- `connection_exception_policy`: the policy

**Returns**:

self

<a name="aea.aea_builder.AEABuilder.set_default_routing"></a>
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

<a name="aea.aea_builder.AEABuilder.set_loop_mode"></a>
#### set`_`loop`_`mode

```python
 | set_loop_mode(loop_mode: Optional[str]) -> "AEABuilder"
```

Set the loop mode.

**Arguments**:

- `loop_mode`: the agent loop mode

**Returns**:

self

<a name="aea.aea_builder.AEABuilder.set_runtime_mode"></a>
#### set`_`runtime`_`mode

```python
 | set_runtime_mode(runtime_mode: Optional[str]) -> "AEABuilder"
```

Set the runtime mode.

**Arguments**:

- `runtime_mode`: the agent runtime mode

**Returns**:

self

<a name="aea.aea_builder.AEABuilder.set_task_manager_mode"></a>
#### set`_`task`_`manager`_`mode

```python
 | set_task_manager_mode(task_manager_mode: Optional[str]) -> "AEABuilder"
```

Set the task_manager_mode.

**Arguments**:

- `task_manager_mode`: the agent task_manager_mode

**Returns**:

self

<a name="aea.aea_builder.AEABuilder.set_storage_uri"></a>
#### set`_`storage`_`uri

```python
 | set_storage_uri(storage_uri: Optional[str]) -> "AEABuilder"
```

Set the storage uri.

**Arguments**:

- `storage_uri`: storage uri

**Returns**:

self

<a name="aea.aea_builder.AEABuilder.set_data_dir"></a>
#### set`_`data`_`dir

```python
 | set_data_dir(data_dir: Optional[str]) -> "AEABuilder"
```

Set the data directory.

**Arguments**:

- `data_dir`: path to directory where to store data.

**Returns**:

self

<a name="aea.aea_builder.AEABuilder.set_logging_config"></a>
#### set`_`logging`_`config

```python
 | set_logging_config(logging_config: Dict) -> "AEABuilder"
```

Set the logging configurations.

The dictionary must satisfy the following schema:

https://docs.python.org/3/library/logging.config.html#logging-config-dictschema

**Arguments**:

- `logging_config`: the logging configurations.

**Returns**:

self

<a name="aea.aea_builder.AEABuilder.set_search_service_address"></a>
#### set`_`search`_`service`_`address

```python
 | set_search_service_address(search_service_address: str) -> "AEABuilder"
```

Set the search service address.

**Arguments**:

- `search_service_address`: the search service address

**Returns**:

self

<a name="aea.aea_builder.AEABuilder.set_name"></a>
#### set`_`name

```python
 | set_name(name: str) -> "AEABuilder"
```

Set the name of the agent.

**Arguments**:

- `name`: the name of the agent.

**Returns**:

the AEABuilder

<a name="aea.aea_builder.AEABuilder.set_default_connection"></a>
#### set`_`default`_`connection

```python
 | set_default_connection(public_id: Optional[PublicId] = None) -> "AEABuilder"
```

Set the default connection.

**Arguments**:

- `public_id`: the public id of the default connection package.

**Returns**:

the AEABuilder

<a name="aea.aea_builder.AEABuilder.add_private_key"></a>
#### add`_`private`_`key

```python
 | add_private_key(identifier: str, private_key_path: Optional[PathLike] = None, is_connection: bool = False) -> "AEABuilder"
```

Add a private key path.

**Arguments**:

- `identifier`: the identifier for that private key path.
- `private_key_path`: an (optional) path to the private key file.
    If None, the key will be created at build time.
- `is_connection`: if the pair is for the connection cryptos

**Returns**:

the AEABuilder

<a name="aea.aea_builder.AEABuilder.remove_private_key"></a>
#### remove`_`private`_`key

```python
 | remove_private_key(identifier: str, is_connection: bool = False) -> "AEABuilder"
```

Remove a private key path by identifier, if present.

**Arguments**:

- `identifier`: the identifier of the private key.
- `is_connection`: if the pair is for the connection cryptos

**Returns**:

the AEABuilder

<a name="aea.aea_builder.AEABuilder.private_key_paths"></a>
#### private`_`key`_`paths

```python
 | @property
 | private_key_paths() -> Dict[str, Optional[str]]
```

Get the private key paths.

<a name="aea.aea_builder.AEABuilder.connection_private_key_paths"></a>
#### connection`_`private`_`key`_`paths

```python
 | @property
 | connection_private_key_paths() -> Dict[str, Optional[str]]
```

Get the connection private key paths.

<a name="aea.aea_builder.AEABuilder.set_default_ledger"></a>
#### set`_`default`_`ledger

```python
 | set_default_ledger(identifier: Optional[str]) -> "AEABuilder"
```

Set a default ledger API to use.

**Arguments**:

- `identifier`: the identifier of the ledger api

**Returns**:

the AEABuilder

<a name="aea.aea_builder.AEABuilder.set_required_ledgers"></a>
#### set`_`required`_`ledgers

```python
 | set_required_ledgers(required_ledgers: Optional[List[str]]) -> "AEABuilder"
```

Set the required ledger identifiers.

These are the ledgers for which the AEA requires a key pair.

**Arguments**:

- `required_ledgers`: the required ledgers.

**Returns**:

the AEABuilder.

<a name="aea.aea_builder.AEABuilder.set_build_entrypoint"></a>
#### set`_`build`_`entrypoint

```python
 | set_build_entrypoint(build_entrypoint: Optional[str]) -> "AEABuilder"
```

Set build entrypoint.

**Arguments**:

- `build_entrypoint`: path to the builder script.

**Returns**:

the AEABuilder

<a name="aea.aea_builder.AEABuilder.set_currency_denominations"></a>
#### set`_`currency`_`denominations

```python
 | set_currency_denominations(currency_denominations: Dict[str, str]) -> "AEABuilder"
```

Set the mapping from ledger ids to currency denominations.

**Arguments**:

- `currency_denominations`: the mapping

**Returns**:

the AEABuilder

<a name="aea.aea_builder.AEABuilder.add_component"></a>
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

- `AEAException`: if a component is already registered with the same component id.   # noqa: DAR402
                    | or if there's a missing dependency.  # noqa: DAR402

**Returns**:

the AEABuilder

<a name="aea.aea_builder.AEABuilder.add_component_instance"></a>
#### add`_`component`_`instance

```python
 | add_component_instance(component: Component) -> "AEABuilder"
```

Add already initialized component object to resources or connections.

Please, pay attention, all dependencies have to be already loaded.

Notice also that this will make the call to 'build()' non re-entrant.
You will have to `reset()` the builder before calling `build()` again.

**Arguments**:

- `component`: Component instance already initialized.

**Returns**:

self

<a name="aea.aea_builder.AEABuilder.set_context_namespace"></a>
#### set`_`context`_`namespace

```python
 | set_context_namespace(context_namespace: Dict[str, Any]) -> "AEABuilder"
```

Set the context namespace.

<a name="aea.aea_builder.AEABuilder.set_agent_pypi_dependencies"></a>
#### set`_`agent`_`pypi`_`dependencies

```python
 | set_agent_pypi_dependencies(dependencies: Dependencies) -> "AEABuilder"
```

Set agent PyPI dependencies.

**Arguments**:

- `dependencies`: PyPI dependencies for the agent.

**Returns**:

the AEABuilder.

<a name="aea.aea_builder.AEABuilder.remove_component"></a>
#### remove`_`component

```python
 | remove_component(component_id: ComponentId) -> "AEABuilder"
```

Remove a component.

**Arguments**:

- `component_id`: the public id of the component.

**Returns**:

the AEABuilder

<a name="aea.aea_builder.AEABuilder.add_protocol"></a>
#### add`_`protocol

```python
 | add_protocol(directory: PathLike) -> "AEABuilder"
```

Add a protocol to the agent.

**Arguments**:

- `directory`: the path to the protocol directory

**Returns**:

the AEABuilder

<a name="aea.aea_builder.AEABuilder.remove_protocol"></a>
#### remove`_`protocol

```python
 | remove_protocol(public_id: PublicId) -> "AEABuilder"
```

Remove protocol.

**Arguments**:

- `public_id`: the public id of the protocol

**Returns**:

the AEABuilder

<a name="aea.aea_builder.AEABuilder.add_connection"></a>
#### add`_`connection

```python
 | add_connection(directory: PathLike) -> "AEABuilder"
```

Add a connection to the agent.

**Arguments**:

- `directory`: the path to the connection directory

**Returns**:

the AEABuilder

<a name="aea.aea_builder.AEABuilder.remove_connection"></a>
#### remove`_`connection

```python
 | remove_connection(public_id: PublicId) -> "AEABuilder"
```

Remove a connection.

**Arguments**:

- `public_id`: the public id of the connection

**Returns**:

the AEABuilder

<a name="aea.aea_builder.AEABuilder.add_skill"></a>
#### add`_`skill

```python
 | add_skill(directory: PathLike) -> "AEABuilder"
```

Add a skill to the agent.

**Arguments**:

- `directory`: the path to the skill directory

**Returns**:

the AEABuilder

<a name="aea.aea_builder.AEABuilder.remove_skill"></a>
#### remove`_`skill

```python
 | remove_skill(public_id: PublicId) -> "AEABuilder"
```

Remove protocol.

**Arguments**:

- `public_id`: the public id of the skill

**Returns**:

the AEABuilder

<a name="aea.aea_builder.AEABuilder.add_contract"></a>
#### add`_`contract

```python
 | add_contract(directory: PathLike) -> "AEABuilder"
```

Add a contract to the agent.

**Arguments**:

- `directory`: the path to the contract directory

**Returns**:

the AEABuilder

<a name="aea.aea_builder.AEABuilder.remove_contract"></a>
#### remove`_`contract

```python
 | remove_contract(public_id: PublicId) -> "AEABuilder"
```

Remove protocol.

**Arguments**:

- `public_id`: the public id of the contract

**Returns**:

the AEABuilder

<a name="aea.aea_builder.AEABuilder.call_all_build_entrypoints"></a>
#### call`_`all`_`build`_`entrypoints

```python
 | call_all_build_entrypoints() -> None
```

Call all the build entrypoints.

<a name="aea.aea_builder.AEABuilder.get_build_root_directory"></a>
#### get`_`build`_`root`_`directory

```python
 | get_build_root_directory() -> str
```

Get build directory root.

<a name="aea.aea_builder.AEABuilder.run_build_for_component_configuration"></a>
#### run`_`build`_`for`_`component`_`configuration

```python
 | @classmethod
 | run_build_for_component_configuration(cls, config: ComponentConfiguration, logger: Optional[logging.Logger] = None) -> None
```

Run a build entrypoint script for component configuration.

<a name="aea.aea_builder.AEABuilder.install_pypi_dependencies"></a>
#### install`_`pypi`_`dependencies

```python
 | install_pypi_dependencies() -> None
```

Install components extra dependencies.

<a name="aea.aea_builder.AEABuilder.build"></a>
#### build

```python
 | build(connection_ids: Optional[Collection[PublicId]] = None, password: Optional[str] = None) -> AEA
```

Build the AEA.

This method is re-entrant only if the components have been
added through the method 'add_component'. If some of them
have been loaded with 'add_component_instance', it
can be called only once, and further calls are only possible
after a call to 'reset' and re-loading of the components added
via 'add_component_instance' and the private keys.

**Arguments**:

- `connection_ids`: select only these connections to run the AEA.
- `password`: the password to encrypt/decrypt the private key.

**Returns**:

the AEA object.

<a name="aea.aea_builder.AEABuilder.get_default_ledger"></a>
#### get`_`default`_`ledger

```python
 | get_default_ledger() -> str
```

Return default ledger.

**Returns**:

the default ledger identifier.

<a name="aea.aea_builder.AEABuilder.get_required_ledgers"></a>
#### get`_`required`_`ledgers

```python
 | get_required_ledgers() -> List[str]
```

Get the required ledger identifiers.

These are the ledgers for which the AEA requires a key pair.

**Returns**:

the list of required ledgers.

<a name="aea.aea_builder.AEABuilder.try_to_load_agent_configuration_file"></a>
#### try`_`to`_`load`_`agent`_`configuration`_`file

```python
 | @classmethod
 | try_to_load_agent_configuration_file(cls, aea_project_path: Union[str, Path]) -> AgentConfig
```

Try to load the agent configuration file..

<a name="aea.aea_builder.AEABuilder.set_from_configuration"></a>
#### set`_`from`_`configuration

```python
 | set_from_configuration(agent_configuration: AgentConfig, aea_project_path: Path, skip_consistency_check: bool = False) -> None
```

Set builder variables from AgentConfig.

**Arguments**:

- `agent_configuration`: AgentConfig to get values from.
- `aea_project_path`: PathLike root directory of the agent project.
- `skip_consistency_check`: if True, the consistency check are skipped.

<a name="aea.aea_builder.AEABuilder.from_aea_project"></a>
#### from`_`aea`_`project

```python
 | @classmethod
 | from_aea_project(cls, aea_project_path: PathLike, skip_consistency_check: bool = False, password: Optional[str] = None) -> "AEABuilder"
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
- `password`: the password to encrypt/decrypt private keys.

**Returns**:

an AEABuilder.

<a name="aea.aea_builder.AEABuilder.get_configuration_file_path"></a>
#### get`_`configuration`_`file`_`path

```python
 | @staticmethod
 | get_configuration_file_path(aea_project_path: Union[Path, str]) -> Path
```

Return path to aea-config file for the given aea project path.

<a name="aea.aea_builder.make_component_logger"></a>
#### make`_`component`_`logger

```python
make_component_logger(configuration: ComponentConfiguration, agent_name: str) -> Optional[logging.Logger]
```

Make the logger for a component.

**Arguments**:

- `configuration`: the component configuration
- `agent_name`: the agent name

**Returns**:

the logger.


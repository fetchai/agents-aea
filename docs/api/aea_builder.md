<a id="aea.aea_builder"></a>

# aea.aea`_`builder

This module contains utilities for building an AEA.

<a id="aea.aea_builder._DependenciesManager"></a>

## `_`DependenciesManager Objects

```python
class _DependenciesManager()
```

Class to manage dependencies of agent packages.

<a id="aea.aea_builder._DependenciesManager.__init__"></a>

#### `__`init`__`

```python
def __init__() -> None
```

Initialize the dependency graph.

<a id="aea.aea_builder._DependenciesManager.all_dependencies"></a>

#### all`_`dependencies

```python
@property
def all_dependencies() -> Set[ComponentId]
```

Get all dependencies.

<a id="aea.aea_builder._DependenciesManager.dependencies_highest_version"></a>

#### dependencies`_`highest`_`version

```python
@property
def dependencies_highest_version() -> Set[ComponentId]
```

Get the dependencies with highest version.

<a id="aea.aea_builder._DependenciesManager.get_components_by_type"></a>

#### get`_`components`_`by`_`type

```python
def get_components_by_type(
    component_type: ComponentType
) -> Dict[ComponentId, ComponentConfiguration]
```

Get the components by type.

<a id="aea.aea_builder._DependenciesManager.protocols"></a>

#### protocols

```python
@property
def protocols() -> Dict[ComponentId, ProtocolConfig]
```

Get the protocols.

<a id="aea.aea_builder._DependenciesManager.connections"></a>

#### connections

```python
@property
def connections() -> Dict[ComponentId, ConnectionConfig]
```

Get the connections.

<a id="aea.aea_builder._DependenciesManager.skills"></a>

#### skills

```python
@property
def skills() -> Dict[ComponentId, SkillConfig]
```

Get the skills.

<a id="aea.aea_builder._DependenciesManager.contracts"></a>

#### contracts

```python
@property
def contracts() -> Dict[ComponentId, ContractConfig]
```

Get the contracts.

<a id="aea.aea_builder._DependenciesManager.add_component"></a>

#### add`_`component

```python
def add_component(configuration: ComponentConfiguration) -> None
```

Add a component to the dependency manager.

**Arguments**:

- `configuration`: the component configuration to add.

<a id="aea.aea_builder._DependenciesManager.remove_component"></a>

#### remove`_`component

```python
def remove_component(component_id: ComponentId) -> None
```

Remove a component.

**Arguments**:

- `component_id`: the component id

**Raises**:

- `ValueError`: if some component depends on this package.

<a id="aea.aea_builder._DependenciesManager.pypi_dependencies"></a>

#### pypi`_`dependencies

```python
@property
def pypi_dependencies() -> Dependencies
```

Get all the PyPI dependencies.

We currently consider only dependency that have the
default PyPI index url and that specify only the
version field.

**Returns**:

the merged PyPI dependencies

<a id="aea.aea_builder._DependenciesManager.install_dependencies"></a>

#### install`_`dependencies

```python
def install_dependencies() -> None
```

Install extra dependencies for components.

<a id="aea.aea_builder.AEABuilder"></a>

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

<a id="aea.aea_builder.AEABuilder.DEFAULT_AGENT_ACT_PERIOD"></a>

#### DEFAULT`_`AGENT`_`ACT`_`PERIOD

seconds

<a id="aea.aea_builder.AEABuilder.__init__"></a>

#### `__`init`__`

```python
def __init__(with_default_packages: bool = True,
             registry_dir: str = DEFAULT_REGISTRY_NAME,
             build_dir_root: Optional[str] = None) -> None
```

Initialize the builder.

**Arguments**:

- `with_default_packages`: add the default packages.
- `registry_dir`: the registry directory.
- `build_dir_root`: the root of the build directory.

<a id="aea.aea_builder.AEABuilder.reset"></a>

#### reset

```python
def reset(is_full_reset: bool = False) -> None
```

Reset the builder.

A full reset causes a reset of all data on the builder. A partial reset
only resets:
    - name,
    - private keys, and
    - component instances

**Arguments**:

- `is_full_reset`: whether it is a full reset or not.

<a id="aea.aea_builder.AEABuilder.set_period"></a>

#### set`_`period

```python
def set_period(period: Optional[float]) -> "AEABuilder"
```

Set agent act period.

**Arguments**:

- `period`: period in seconds

**Returns**:

self

<a id="aea.aea_builder.AEABuilder.set_execution_timeout"></a>

#### set`_`execution`_`timeout

```python
def set_execution_timeout(execution_timeout: Optional[float]) -> "AEABuilder"
```

Set agent execution timeout in seconds.

**Arguments**:

- `execution_timeout`: execution_timeout in seconds

**Returns**:

self

<a id="aea.aea_builder.AEABuilder.set_max_reactions"></a>

#### set`_`max`_`reactions

```python
def set_max_reactions(max_reactions: Optional[int]) -> "AEABuilder"
```

Set agent max reaction in one react.

**Arguments**:

- `max_reactions`: int

**Returns**:

self

<a id="aea.aea_builder.AEABuilder.set_decision_maker_handler_details"></a>

#### set`_`decision`_`maker`_`handler`_`details

```python
def set_decision_maker_handler_details(decision_maker_handler_dotted_path: str,
                                       file_path: str,
                                       config: Dict[str, Any]) -> "AEABuilder"
```

Set error handler details.

**Arguments**:

- `decision_maker_handler_dotted_path`: the dotted path to the decision maker handler
- `file_path`: the file path to the file which contains the decision maker handler
- `config`: the configuration passed to the decision maker handler on instantiation

**Returns**:

self

<a id="aea.aea_builder.AEABuilder.set_error_handler_details"></a>

#### set`_`error`_`handler`_`details

```python
def set_error_handler_details(error_handler_dotted_path: str, file_path: str,
                              config: Dict[str, Any]) -> "AEABuilder"
```

Set error handler details.

**Arguments**:

- `error_handler_dotted_path`: the dotted path to the error handler
- `file_path`: the file path to the file which contains the error handler
- `config`: the configuration passed to the error handler on instantiation

**Returns**:

self

<a id="aea.aea_builder.AEABuilder.set_skill_exception_policy"></a>

#### set`_`skill`_`exception`_`policy

```python
def set_skill_exception_policy(
        skill_exception_policy: Optional[ExceptionPolicyEnum]) -> "AEABuilder"
```

Set skill exception policy.

**Arguments**:

- `skill_exception_policy`: the policy

**Returns**:

self

<a id="aea.aea_builder.AEABuilder.set_connection_exception_policy"></a>

#### set`_`connection`_`exception`_`policy

```python
def set_connection_exception_policy(
    connection_exception_policy: Optional[ExceptionPolicyEnum]
) -> "AEABuilder"
```

Set connection exception policy.

**Arguments**:

- `connection_exception_policy`: the policy

**Returns**:

self

<a id="aea.aea_builder.AEABuilder.set_default_routing"></a>

#### set`_`default`_`routing

```python
def set_default_routing(
        default_routing: Dict[PublicId, PublicId]) -> "AEABuilder"
```

Set default routing.

This is a map from public ids (protocols) to public ids (connections).

**Arguments**:

- `default_routing`: the default routing mapping

**Returns**:

self

<a id="aea.aea_builder.AEABuilder.set_loop_mode"></a>

#### set`_`loop`_`mode

```python
def set_loop_mode(loop_mode: Optional[str]) -> "AEABuilder"
```

Set the loop mode.

**Arguments**:

- `loop_mode`: the agent loop mode

**Returns**:

self

<a id="aea.aea_builder.AEABuilder.set_runtime_mode"></a>

#### set`_`runtime`_`mode

```python
def set_runtime_mode(runtime_mode: Optional[str]) -> "AEABuilder"
```

Set the runtime mode.

**Arguments**:

- `runtime_mode`: the agent runtime mode

**Returns**:

self

<a id="aea.aea_builder.AEABuilder.set_task_manager_mode"></a>

#### set`_`task`_`manager`_`mode

```python
def set_task_manager_mode(task_manager_mode: Optional[str]) -> "AEABuilder"
```

Set the task_manager_mode.

**Arguments**:

- `task_manager_mode`: the agent task_manager_mode

**Returns**:

self

<a id="aea.aea_builder.AEABuilder.set_storage_uri"></a>

#### set`_`storage`_`uri

```python
def set_storage_uri(storage_uri: Optional[str]) -> "AEABuilder"
```

Set the storage uri.

**Arguments**:

- `storage_uri`: storage uri

**Returns**:

self

<a id="aea.aea_builder.AEABuilder.set_data_dir"></a>

#### set`_`data`_`dir

```python
def set_data_dir(data_dir: Optional[str]) -> "AEABuilder"
```

Set the data directory.

**Arguments**:

- `data_dir`: path to directory where to store data.

**Returns**:

self

<a id="aea.aea_builder.AEABuilder.set_logging_config"></a>

#### set`_`logging`_`config

```python
def set_logging_config(logging_config: Dict) -> "AEABuilder"
```

Set the logging configurations.

The dictionary must satisfy the following schema:

  https://docs.python.org/3/library/logging.config.html#logging-config-dictschema

**Arguments**:

- `logging_config`: the logging configurations.

**Returns**:

self

<a id="aea.aea_builder.AEABuilder.set_search_service_address"></a>

#### set`_`search`_`service`_`address

```python
def set_search_service_address(search_service_address: str) -> "AEABuilder"
```

Set the search service address.

**Arguments**:

- `search_service_address`: the search service address

**Returns**:

self

<a id="aea.aea_builder.AEABuilder.set_name"></a>

#### set`_`name

```python
def set_name(name: str) -> "AEABuilder"
```

Set the name of the agent.

**Arguments**:

- `name`: the name of the agent.

**Returns**:

the AEABuilder

<a id="aea.aea_builder.AEABuilder.set_default_connection"></a>

#### set`_`default`_`connection

```python
def set_default_connection(
        public_id: Optional[PublicId] = None) -> "AEABuilder"
```

Set the default connection.

**Arguments**:

- `public_id`: the public id of the default connection package.

**Returns**:

the AEABuilder

<a id="aea.aea_builder.AEABuilder.add_private_key"></a>

#### add`_`private`_`key

```python
def add_private_key(identifier: str,
                    private_key_path: Optional[PathLike] = None,
                    is_connection: bool = False) -> "AEABuilder"
```

Add a private key path.

**Arguments**:

- `identifier`: the identifier for that private key path.
- `private_key_path`: an (optional) path to the private key file.
If None, the key will be created at build time.
- `is_connection`: if the pair is for the connection cryptos

**Returns**:

the AEABuilder

<a id="aea.aea_builder.AEABuilder.remove_private_key"></a>

#### remove`_`private`_`key

```python
def remove_private_key(identifier: str,
                       is_connection: bool = False) -> "AEABuilder"
```

Remove a private key path by identifier, if present.

**Arguments**:

- `identifier`: the identifier of the private key.
- `is_connection`: if the pair is for the connection cryptos

**Returns**:

the AEABuilder

<a id="aea.aea_builder.AEABuilder.private_key_paths"></a>

#### private`_`key`_`paths

```python
@property
def private_key_paths() -> Dict[str, Optional[str]]
```

Get the private key paths.

<a id="aea.aea_builder.AEABuilder.connection_private_key_paths"></a>

#### connection`_`private`_`key`_`paths

```python
@property
def connection_private_key_paths() -> Dict[str, Optional[str]]
```

Get the connection private key paths.

<a id="aea.aea_builder.AEABuilder.set_default_ledger"></a>

#### set`_`default`_`ledger

```python
def set_default_ledger(identifier: Optional[str]) -> "AEABuilder"
```

Set a default ledger API to use.

**Arguments**:

- `identifier`: the identifier of the ledger api

**Returns**:

the AEABuilder

<a id="aea.aea_builder.AEABuilder.set_required_ledgers"></a>

#### set`_`required`_`ledgers

```python
def set_required_ledgers(
        required_ledgers: Optional[List[str]]) -> "AEABuilder"
```

Set the required ledger identifiers.

These are the ledgers for which the AEA requires a key pair.

**Arguments**:

- `required_ledgers`: the required ledgers.

**Returns**:

the AEABuilder.

<a id="aea.aea_builder.AEABuilder.set_build_entrypoint"></a>

#### set`_`build`_`entrypoint

```python
def set_build_entrypoint(build_entrypoint: Optional[str]) -> "AEABuilder"
```

Set build entrypoint.

**Arguments**:

- `build_entrypoint`: path to the builder script.

**Returns**:

the AEABuilder

<a id="aea.aea_builder.AEABuilder.set_currency_denominations"></a>

#### set`_`currency`_`denominations

```python
def set_currency_denominations(
        currency_denominations: Dict[str, str]) -> "AEABuilder"
```

Set the mapping from ledger ids to currency denominations.

**Arguments**:

- `currency_denominations`: the mapping

**Returns**:

the AEABuilder

<a id="aea.aea_builder.AEABuilder.add_component"></a>

#### add`_`component

```python
def add_component(component_type: ComponentType,
                  directory: PathLike,
                  skip_consistency_check: bool = False) -> "AEABuilder"
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

<a id="aea.aea_builder.AEABuilder.add_component_instance"></a>

#### add`_`component`_`instance

```python
def add_component_instance(component: Component) -> "AEABuilder"
```

Add already initialized component object to resources or connections.

Please, pay attention, all dependencies have to be already loaded.

Notice also that this will make the call to 'build()' non re-entrant.
You will have to `reset()` the builder before calling `build()` again.

**Arguments**:

- `component`: Component instance already initialized.

**Returns**:

self

<a id="aea.aea_builder.AEABuilder.set_context_namespace"></a>

#### set`_`context`_`namespace

```python
def set_context_namespace(context_namespace: Dict[str, Any]) -> "AEABuilder"
```

Set the context namespace.

<a id="aea.aea_builder.AEABuilder.set_agent_pypi_dependencies"></a>

#### set`_`agent`_`pypi`_`dependencies

```python
def set_agent_pypi_dependencies(dependencies: Dependencies) -> "AEABuilder"
```

Set agent PyPI dependencies.

**Arguments**:

- `dependencies`: PyPI dependencies for the agent.

**Returns**:

the AEABuilder.

<a id="aea.aea_builder.AEABuilder.remove_component"></a>

#### remove`_`component

```python
def remove_component(component_id: ComponentId) -> "AEABuilder"
```

Remove a component.

**Arguments**:

- `component_id`: the public id of the component.

**Returns**:

the AEABuilder

<a id="aea.aea_builder.AEABuilder.add_protocol"></a>

#### add`_`protocol

```python
def add_protocol(directory: PathLike) -> "AEABuilder"
```

Add a protocol to the agent.

**Arguments**:

- `directory`: the path to the protocol directory

**Returns**:

the AEABuilder

<a id="aea.aea_builder.AEABuilder.remove_protocol"></a>

#### remove`_`protocol

```python
def remove_protocol(public_id: PublicId) -> "AEABuilder"
```

Remove protocol.

**Arguments**:

- `public_id`: the public id of the protocol

**Returns**:

the AEABuilder

<a id="aea.aea_builder.AEABuilder.add_connection"></a>

#### add`_`connection

```python
def add_connection(directory: PathLike) -> "AEABuilder"
```

Add a connection to the agent.

**Arguments**:

- `directory`: the path to the connection directory

**Returns**:

the AEABuilder

<a id="aea.aea_builder.AEABuilder.remove_connection"></a>

#### remove`_`connection

```python
def remove_connection(public_id: PublicId) -> "AEABuilder"
```

Remove a connection.

**Arguments**:

- `public_id`: the public id of the connection

**Returns**:

the AEABuilder

<a id="aea.aea_builder.AEABuilder.add_skill"></a>

#### add`_`skill

```python
def add_skill(directory: PathLike) -> "AEABuilder"
```

Add a skill to the agent.

**Arguments**:

- `directory`: the path to the skill directory

**Returns**:

the AEABuilder

<a id="aea.aea_builder.AEABuilder.remove_skill"></a>

#### remove`_`skill

```python
def remove_skill(public_id: PublicId) -> "AEABuilder"
```

Remove protocol.

**Arguments**:

- `public_id`: the public id of the skill

**Returns**:

the AEABuilder

<a id="aea.aea_builder.AEABuilder.add_contract"></a>

#### add`_`contract

```python
def add_contract(directory: PathLike) -> "AEABuilder"
```

Add a contract to the agent.

**Arguments**:

- `directory`: the path to the contract directory

**Returns**:

the AEABuilder

<a id="aea.aea_builder.AEABuilder.remove_contract"></a>

#### remove`_`contract

```python
def remove_contract(public_id: PublicId) -> "AEABuilder"
```

Remove protocol.

**Arguments**:

- `public_id`: the public id of the contract

**Returns**:

the AEABuilder

<a id="aea.aea_builder.AEABuilder.call_all_build_entrypoints"></a>

#### call`_`all`_`build`_`entrypoints

```python
def call_all_build_entrypoints() -> None
```

Call all the build entrypoints.

<a id="aea.aea_builder.AEABuilder.get_build_root_directory"></a>

#### get`_`build`_`root`_`directory

```python
def get_build_root_directory() -> str
```

Get build directory root.

<a id="aea.aea_builder.AEABuilder.run_build_for_component_configuration"></a>

#### run`_`build`_`for`_`component`_`configuration

```python
@classmethod
def run_build_for_component_configuration(
        cls,
        config: ComponentConfiguration,
        logger: Optional[logging.Logger] = None) -> None
```

Run a build entrypoint script for component configuration.

<a id="aea.aea_builder.AEABuilder.install_pypi_dependencies"></a>

#### install`_`pypi`_`dependencies

```python
def install_pypi_dependencies() -> None
```

Install components extra dependencies.

<a id="aea.aea_builder.AEABuilder.build"></a>

#### build

```python
def build(connection_ids: Optional[Collection[PublicId]] = None,
          password: Optional[str] = None) -> AEA
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

<a id="aea.aea_builder.AEABuilder.get_default_ledger"></a>

#### get`_`default`_`ledger

```python
def get_default_ledger() -> str
```

Return default ledger.

**Returns**:

the default ledger identifier.

<a id="aea.aea_builder.AEABuilder.get_required_ledgers"></a>

#### get`_`required`_`ledgers

```python
def get_required_ledgers() -> List[str]
```

Get the required ledger identifiers.

These are the ledgers for which the AEA requires a key pair.

**Returns**:

the list of required ledgers.

<a id="aea.aea_builder.AEABuilder.check_project_dependencies"></a>

#### check`_`project`_`dependencies

```python
@staticmethod
def check_project_dependencies(agent_configuration: AgentConfig,
                               project_path: Path) -> None
```

Check project config for missing dependencies.

<a id="aea.aea_builder.AEABuilder.try_to_load_agent_configuration_file"></a>

#### try`_`to`_`load`_`agent`_`configuration`_`file

```python
@classmethod
def try_to_load_agent_configuration_file(
        cls,
        aea_project_path: Union[str, Path],
        apply_environment_variables: bool = True) -> AgentConfig
```

Try to load the agent configuration file..

<a id="aea.aea_builder.AEABuilder.set_from_configuration"></a>

#### set`_`from`_`configuration

```python
def set_from_configuration(agent_configuration: AgentConfig,
                           aea_project_path: Path,
                           skip_consistency_check: bool = False) -> None
```

Set builder variables from AgentConfig.

**Arguments**:

- `agent_configuration`: AgentConfig to get values from.
- `aea_project_path`: PathLike root directory of the agent project.
- `skip_consistency_check`: if True, the consistency check are skipped.

<a id="aea.aea_builder.AEABuilder.from_aea_project"></a>

#### from`_`aea`_`project

```python
@classmethod
def from_aea_project(cls,
                     aea_project_path: PathLike,
                     skip_consistency_check: bool = False,
                     apply_environment_variables: bool = False,
                     password: Optional[str] = None) -> "AEABuilder"
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
- `apply_environment_variables`: if True, environment variables are loaded.
- `password`: the password to encrypt/decrypt private keys.

**Returns**:

an AEABuilder.

<a id="aea.aea_builder.AEABuilder.get_configuration_file_path"></a>

#### get`_`configuration`_`file`_`path

```python
@staticmethod
def get_configuration_file_path(aea_project_path: Union[Path, str]) -> Path
```

Return path to aea-config file for the given AEA project path.

<a id="aea.aea_builder.make_component_logger"></a>

#### make`_`component`_`logger

```python
def make_component_logger(configuration: ComponentConfiguration,
                          agent_name: str) -> Optional[logging.Logger]
```

Make the logger for a component.

**Arguments**:

- `configuration`: the component configuration
- `agent_name`: the agent name

**Returns**:

the logger.


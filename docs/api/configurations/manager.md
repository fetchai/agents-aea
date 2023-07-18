<a id="aea.configurations.manager"></a>

# aea.configurations.manager

Implementation of the AgentConfigManager.

<a id="aea.configurations.manager.RESOURCE_TYPE_TO_CONFIG_FILE"></a>

#### RESOURCE`_`TYPE`_`TO`_`CONFIG`_`FILE

type: Dict[str, str]

<a id="aea.configurations.manager.VariableDoesNotExist"></a>

## VariableDoesNotExist Objects

```python
class VariableDoesNotExist(ValueError)
```

Variable does not exist in a config exception.

<a id="aea.configurations.manager.handle_dotted_path"></a>

#### handle`_`dotted`_`path

```python
def handle_dotted_path(
    value: str,
    author: str,
    aea_project_path: Union[str, Path] = "."
) -> Tuple[List[str], Path, ConfigLoader, Optional[ComponentId]]
```

Separate the path between path to resource and json path to attribute.

Allowed values:
    'agent.an_attribute_name'
    'protocols.my_protocol.an_attribute_name'
    'connections.my_connection.an_attribute_name'
    'contracts.my_contract.an_attribute_name'
    'skills.my_skill.an_attribute_name'
    'vendor.author.[protocols|contracts|connections|skills].package_name.attribute_name

We also return the component id to retrieve the configuration of a specific
component. Notice that at this point we don't know the version,
so we put 'latest' as version, but later we will ignore it because
we will filter with only the component prefix (i.e. the triple type, author and name).

**Arguments**:

- `value`: dotted path.
- `author`: the author string.
- `aea_project_path`: project path

**Returns**:

Tuple[list of settings dict keys, filepath, config loader, component id].

<a id="aea.configurations.manager.find_component_directory_from_component_id"></a>

#### find`_`component`_`directory`_`from`_`component`_`id

```python
def find_component_directory_from_component_id(
        aea_project_directory: Path, component_id: ComponentId) -> Path
```

Find a component directory from component id.

<a id="aea.configurations.manager.AgentConfigManager"></a>

## AgentConfigManager Objects

```python
class AgentConfigManager()
```

AeaConfig manager.

<a id="aea.configurations.manager.AgentConfigManager.__init__"></a>

#### `__`init`__`

```python
def __init__(agent_config: AgentConfig,
             aea_project_directory: Union[str, Path],
             env_vars_friendly: bool = False) -> None
```

Init manager.

**Arguments**:

- `agent_config`: AgentConfig to manage.
- `aea_project_directory`: directory where project for agent_config placed.
- `env_vars_friendly`: whether or not it is env vars friendly

<a id="aea.configurations.manager.AgentConfigManager.load_component_configuration"></a>

#### load`_`component`_`configuration

```python
def load_component_configuration(
        component_id: ComponentId,
        skip_consistency_check: bool = True) -> ComponentConfiguration
```

Load component configuration from the project directory.

**Arguments**:

- `component_id`: Id of the component to load config for.
- `skip_consistency_check`: bool.

**Returns**:

ComponentConfiguration

<a id="aea.configurations.manager.AgentConfigManager.agent_config_file_path"></a>

#### agent`_`config`_`file`_`path

```python
@property
def agent_config_file_path() -> Path
```

Return agent config file path.

<a id="aea.configurations.manager.AgentConfigManager.load"></a>

#### load

```python
@classmethod
def load(cls,
         aea_project_path: Union[Path, str],
         substitude_env_vars: bool = False) -> "AgentConfigManager"
```

Create AgentConfigManager instance from agent project path.

<a id="aea.configurations.manager.AgentConfigManager.set_variable"></a>

#### set`_`variable

```python
def set_variable(path: VariablePath, value: JSON_TYPES) -> None
```

Set config variable.

**Arguments**:

- `path`: str dotted path  or List[Union[ComponentId, str]]
- `value`: one of the json friendly objects.

<a id="aea.configurations.manager.AgentConfigManager.get_variable"></a>

#### get`_`variable

```python
def get_variable(path: VariablePath) -> JSON_TYPES
```

Set config variable.

**Arguments**:

- `path`: str dotted path or List[Union[ComponentId, str]]

**Returns**:

json friendly value.

<a id="aea.configurations.manager.AgentConfigManager.update_config"></a>

#### update`_`config

```python
def update_config(overrides: Dict,
                  dict_overrides: Optional[Dict] = None) -> None
```

Apply overrides for agent config.

Validates and applies agent config and component overrides.
Does not save it on the disc!

**Arguments**:

- `overrides`: overridden values dictionary
- `dict_overrides`: A dictionary containing mapping for Component ID -> List of paths

**Returns**:

None

<a id="aea.configurations.manager.AgentConfigManager.validate_current_config"></a>

#### validate`_`current`_`config

```python
def validate_current_config() -> None
```

Check is current config valid.

<a id="aea.configurations.manager.AgentConfigManager.json"></a>

#### json

```python
@property
def json() -> Dict
```

Return current agent config json representation.

<a id="aea.configurations.manager.AgentConfigManager.dump_config"></a>

#### dump`_`config

```python
def dump_config() -> None
```

Save agent config on the disc.

<a id="aea.configurations.manager.AgentConfigManager.verify_private_keys"></a>

#### verify`_`private`_`keys

```python
@classmethod
def verify_private_keys(
        cls,
        aea_project_path: Union[Path, str],
        private_key_helper: Callable[[AgentConfig, Path, Optional[str]], None],
        substitude_env_vars: bool = False,
        password: Optional[str] = None) -> "AgentConfigManager"
```

Verify private keys.

Does not saves the config! Use AgentConfigManager.dump_config()

**Arguments**:

- `aea_project_path`: path to an AEA project.
- `private_key_helper`: private_key_helper is a function that use agent config to check the keys
- `substitude_env_vars`: replace env vars with values, does not dump config
- `password`: the password to encrypt/decrypt the private key.

**Returns**:

the agent configuration manager.

<a id="aea.configurations.manager.AgentConfigManager.get_overridables"></a>

#### get`_`overridables

```python
def get_overridables() -> Tuple[Dict, Dict[ComponentId, Dict]]
```

Get config overridables.


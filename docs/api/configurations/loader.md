<a name="aea.configurations.loader"></a>
# aea.configurations.loader

Implementation of the parser for configuration file.

<a name="aea.configurations.loader.make_jsonschema_base_uri"></a>
#### make`_`jsonschema`_`base`_`uri

```python
make_jsonschema_base_uri(base_uri_path: Path) -> str
```

Make the JSONSchema base URI, cross-platform.

**Arguments**:

- `base_uri_path`: the path to the base directory.

**Returns**:

the string in URI form.

<a name="aea.configurations.loader.BaseConfigLoader"></a>
## BaseConfigLoader Objects

```python
class BaseConfigLoader()
```

Base class for configuration loader classes.

<a name="aea.configurations.loader.BaseConfigLoader.__init__"></a>
#### `__`init`__`

```python
 | __init__(schema_filename: str)
```

Initialize the base configuration loader.

**Arguments**:

- `schema_filename`: the path to the schema.

<a name="aea.configurations.loader.BaseConfigLoader.validator"></a>
#### validator

```python
 | @property
 | validator() -> Draft4Validator
```

Get the json schema validator.

<a name="aea.configurations.loader.BaseConfigLoader.validate"></a>
#### validate

```python
 | validate(json_data: Dict) -> None
```

Validate a JSON object.

**Arguments**:

- `json_data`: the JSON data.

**Returns**:

None.

<a name="aea.configurations.loader.BaseConfigLoader.required_fields"></a>
#### required`_`fields

```python
 | @property
 | required_fields() -> List[str]
```

Get the required fields.

**Returns**:

list of required fields.

<a name="aea.configurations.loader.ConfigLoader"></a>
## ConfigLoader Objects

```python
class ConfigLoader(Generic[T],  BaseConfigLoader)
```

Parsing, serialization and validation for package configuration files.

<a name="aea.configurations.loader.ConfigLoader.__init__"></a>
#### `__`init`__`

```python
 | __init__(schema_filename: str, configuration_class: Type[T])
```

Initialize the parser for configuration files.

**Arguments**:

- `schema_filename`: the path to the JSON-schema file in 'aea/configurations/schemas'.
- `configuration_class`: the configuration class (e.g. AgentConfig, SkillConfig etc.)

<a name="aea.configurations.loader.ConfigLoader.configuration_class"></a>
#### configuration`_`class

```python
 | @property
 | configuration_class() -> Type[T]
```

Get the configuration class of the loader.

<a name="aea.configurations.loader.ConfigLoader.load_protocol_specification"></a>
#### load`_`protocol`_`specification

```python
 | load_protocol_specification(file_pointer: TextIO) -> T
```

Load an agent configuration file.

**Arguments**:

- `file_pointer`: the file pointer to the configuration file

**Returns**:

the configuration object.
:raises

<a name="aea.configurations.loader.ConfigLoader.validate"></a>
#### validate

```python
 | validate(json_data: Dict) -> None
```

Validate a JSON object.

**Arguments**:

- `json_data`: the JSON data.

**Returns**:

None.

<a name="aea.configurations.loader.ConfigLoader.load"></a>
#### load

```python
 | load(file_pointer: TextIO) -> T
```

Load a configuration file.

**Arguments**:

- `file_pointer`: the file pointer to the configuration file

**Returns**:

the configuration object.

<a name="aea.configurations.loader.ConfigLoader.dump"></a>
#### dump

```python
 | dump(configuration: T, file_pointer: TextIO) -> None
```

Dump a configuration.

**Arguments**:

- `configuration`: the configuration to be dumped.
- `file_pointer`: the file pointer to the configuration file

**Returns**:

None

<a name="aea.configurations.loader.ConfigLoader.from_configuration_type"></a>
#### from`_`configuration`_`type

```python
 | @classmethod
 | from_configuration_type(cls, configuration_type: Union[PackageType, str]) -> "ConfigLoader"
```

Get the configuration loader from the type.

<a name="aea.configurations.loader.ConfigLoader.load_agent_config_from_json"></a>
#### load`_`agent`_`config`_`from`_`json

```python
 | load_agent_config_from_json(configuration_json: List[Dict]) -> AgentConfig
```

Load agent configuration from configuration json data.

**Arguments**:

- `configuration_json`: list of dicts with aea configuration

**Returns**:

AgentConfig instance

<a name="aea.configurations.loader.ConfigLoaders"></a>
## ConfigLoaders Objects

```python
class ConfigLoaders()
```

Configuration Loader class to load any package type.

<a name="aea.configurations.loader.ConfigLoaders.from_package_type"></a>
#### from`_`package`_`type

```python
 | @classmethod
 | from_package_type(cls, configuration_type: Union[PackageType, str]) -> "ConfigLoader"
```

Get a config loader from the configuration type.

**Arguments**:

- `configuration_type`: the configuration type

<a name="aea.configurations.loader.load_component_configuration"></a>
#### load`_`component`_`configuration

```python
load_component_configuration(component_type: ComponentType, directory: Path, skip_consistency_check: bool = False) -> "ComponentConfiguration"
```

Load configuration and check that it is consistent against the directory.

**Arguments**:

- `component_type`: the component type.
- `directory`: the root of the package
- `skip_consistency_check`: if True, the consistency check are skipped.

**Returns**:

the configuration object.


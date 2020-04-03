<a name=".aea.configurations.loader"></a>
## aea.configurations.loader

Implementation of the parser for configuration file.

<a name=".aea.configurations.loader.ConfigLoader"></a>
### ConfigLoader

```python
class ConfigLoader(Generic[T])
```

This class implement parsing, serialization and validation functionalities for the 'aea' configuration files.

<a name=".aea.configurations.loader.ConfigLoader.__init__"></a>
#### `__`init`__`

```python
 | __init__(schema_filename: str, configuration_class: Type[T])
```

Initialize the parser for configuration files.

**Arguments**:

- `schema_filename`: the path to the JSON-schema file in 'aea/configurations/schemas'.
- `configuration_class`: the configuration class (e.g. AgentConfig, SkillConfig etc.)

<a name=".aea.configurations.loader.ConfigLoader.validator"></a>
#### validator

```python
 | @property
 | validator() -> Draft4Validator
```

Get the json schema validator.

<a name=".aea.configurations.loader.ConfigLoader.configuration_class"></a>
#### configuration`_`class

```python
 | @property
 | configuration_class() -> Type[T]
```

Get the configuration type of the loader.

<a name=".aea.configurations.loader.ConfigLoader.load_protocol_specification"></a>
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

<a name=".aea.configurations.loader.ConfigLoader.load"></a>
#### load

```python
 | load(file_pointer: TextIO) -> T
```

Load an agent configuration file.

**Arguments**:

- `file_pointer`: the file pointer to the configuration file

**Returns**:

the configuration object.
:raises

<a name=".aea.configurations.loader.ConfigLoader.dump"></a>
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

<a name=".aea.configurations.loader.ConfigLoader.from_configuration_type"></a>
#### from`_`configuration`_`type

```python
 | @classmethod
 | from_configuration_type(cls, configuration_type: Union[ConfigurationType, str]) -> "ConfigLoader"
```

Get the configuration loader from the type.


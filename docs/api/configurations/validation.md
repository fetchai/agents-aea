<a id="aea.configurations.validation"></a>

# aea.configurations.validation

Implementation of the configuration validation.

<a id="aea.configurations.validation.make_jsonschema_base_uri"></a>

#### make`_`jsonschema`_`base`_`uri

```python
def make_jsonschema_base_uri(base_uri_path: Path) -> str
```

Make the JSONSchema base URI, cross-platform.

**Arguments**:

- `base_uri_path`: the path to the base directory.

**Returns**:

the string in URI form.

<a id="aea.configurations.validation.ExtraPropertiesError"></a>

## ExtraPropertiesError Objects

```python
class ExtraPropertiesError(ValueError)
```

Extra properties exception.

<a id="aea.configurations.validation.ExtraPropertiesError.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Get string representation of the object.

<a id="aea.configurations.validation.ExtraPropertiesError.__repr__"></a>

#### `__`repr`__`

```python
def __repr__() -> str
```

Get string representation of the object.

<a id="aea.configurations.validation.CustomTypeChecker"></a>

## CustomTypeChecker Objects

```python
class CustomTypeChecker(TypeChecker)
```

Custom type checker to handle env variables.

<a id="aea.configurations.validation.CustomTypeChecker.is_type"></a>

#### is`_`type

```python
def is_type(instance, type) -> bool
```

Check is instance of type.

<a id="aea.configurations.validation.own_additional_properties"></a>

#### own`_`additional`_`properties

```python
def own_additional_properties(validator, aP, instance, schema) -> Iterator
```

Additional properties validator.

<a id="aea.configurations.validation.ConfigValidator"></a>

## ConfigValidator Objects

```python
class ConfigValidator()
```

Configuration validator implementation.

<a id="aea.configurations.validation.ConfigValidator.__init__"></a>

#### `__`init`__`

```python
def __init__(schema_filename: str, env_vars_friendly: bool = False) -> None
```

Initialize the parser for configuration files.

**Arguments**:

- `schema_filename`: the path to the JSON-schema file in 'aea/configurations/schemas'.
- `env_vars_friendly`: whether or not it is env var friendly.

<a id="aea.configurations.validation.ConfigValidator.split_component_id_and_config"></a>

#### split`_`component`_`id`_`and`_`config

```python
@staticmethod
def split_component_id_and_config(
        component_index: int,
        component_configuration_json: Dict) -> ComponentId
```

Split component id and configuration.

**Arguments**:

- `component_index`: the position of the component configuration in the agent config file..
- `component_configuration_json`: the JSON object to process.

**Raises**:

- `ValueError`: if the component id cannot be extracted.

**Returns**:

the component id and the configuration object.

<a id="aea.configurations.validation.ConfigValidator.validate_component_configuration"></a>

#### validate`_`component`_`configuration

```python
@classmethod
def validate_component_configuration(cls,
                                     component_id: ComponentId,
                                     configuration: Dict,
                                     env_vars_friendly: bool = False) -> None
```

Validate the component configuration of an agent configuration file.

This check is to detect inconsistencies in the specified fields.

**Arguments**:

- `component_id`: the component id.
- `configuration`: the configuration dictionary.
- `env_vars_friendly`: bool, if set True, will not raise errors over the env variable definitions.

**Raises**:

- `ValueError`: if the configuration is not valid.

<a id="aea.configurations.validation.ConfigValidator.validate"></a>

#### validate

```python
def validate(json_data: Dict) -> None
```

Validate a JSON object against the right JSON schema.

**Arguments**:

- `json_data`: the JSON data.

<a id="aea.configurations.validation.ConfigValidator.validate_agent_components_configuration"></a>

#### validate`_`agent`_`components`_`configuration

```python
def validate_agent_components_configuration(
        component_configurations: Dict) -> None
```

Validate agent component configurations overrides.

**Arguments**:

- `component_configurations`: the component configurations to validate.

<a id="aea.configurations.validation.ConfigValidator.required_fields"></a>

#### required`_`fields

```python
@property
def required_fields() -> List[str]
```

Get the required fields.

**Returns**:

list of required fields.

<a id="aea.configurations.validation.validate_data_with_pattern"></a>

#### validate`_`data`_`with`_`pattern

```python
def validate_data_with_pattern(data: dict,
                               pattern: dict,
                               excludes: Optional[List[Tuple[str]]] = None,
                               skip_env_vars: bool = False) -> List[str]
```

Validate data dict with pattern dict for attributes present and type match.

**Arguments**:

- `data`: data dict to validate
- `pattern`: dict with pattern to check over
- `excludes`: list of tuples of str of paths to be skipped during the check
- `skip_env_vars`: is set True will not check data type over env variables.

**Returns**:

list of str with error descriptions

<a id="aea.configurations.validation.filter_data"></a>

#### filter`_`data

```python
def filter_data(base: Any, updates: Any) -> Any
```

Return difference in values or `SAME_MARK` object if values are the same.


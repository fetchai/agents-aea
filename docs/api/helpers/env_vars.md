<a id="aea.helpers.env_vars"></a>

# aea.helpers.env`_`vars

Implementation of the environment variables support.

<a id="aea.helpers.env_vars.is_env_variable"></a>

#### is`_`env`_`variable

```python
def is_env_variable(value: Any) -> bool
```

Check is variable string with env variable pattern.

<a id="aea.helpers.env_vars.export_path_to_env_var_string"></a>

#### export`_`path`_`to`_`env`_`var`_`string

```python
def export_path_to_env_var_string(export_path: List[str]) -> str
```

Conver export path to environment variable string.

<a id="aea.helpers.env_vars.replace_with_env_var"></a>

#### replace`_`with`_`env`_`var

```python
def replace_with_env_var(value: str, env_variables: dict, default_value: Any = NotSet, default_var_name: Optional[str] = None) -> JSON_TYPES
```

Replace env var with value.

<a id="aea.helpers.env_vars.apply_env_variables"></a>

#### apply`_`env`_`variables

```python
def apply_env_variables(data: Union[Dict, List[Dict]], env_variables: Mapping[str, Any], path: Optional[List[str]] = None, default_value: Any = NotSet) -> JSON_TYPES
```

Create new resulting dict with env variables applied.

<a id="aea.helpers.env_vars.convert_value_str_to_type"></a>

#### convert`_`value`_`str`_`to`_`type

```python
def convert_value_str_to_type(value: str, type_str: str) -> JSON_TYPES
```

Convert value by type name to native python type.

<a id="aea.helpers.env_vars.apply_env_variables_on_agent_config"></a>

#### apply`_`env`_`variables`_`on`_`agent`_`config

```python
def apply_env_variables_on_agent_config(data: List[Dict], env_variables: Mapping[str, Any]) -> List[Dict]
```

Create new resulting dict with env variables applied.

<a id="aea.helpers.env_vars.is_strict_list"></a>

#### is`_`strict`_`list

```python
def is_strict_list(data: Union[List, Tuple]) -> bool
```

Check if a data list is an strict list

The data list contains a mapping object we need to process it as an
object containing configurable parameters. For example

cert_requests:
- public_key: example_public_key

This will get exported as `CONNECTION_NAME_CERT_REQUESTS_0_PUBLIC_KEY=example_public_key`

Where as

parameters:
- hello
- world

will get exported as `SKILL_NAME_PARAMETERS=["hello", "world"]`

**Arguments**:

- `data`: Data list

**Returns**:

Boolean specifying whether it's a strict list or not

<a id="aea.helpers.env_vars.generate_env_vars_recursively"></a>

#### generate`_`env`_`vars`_`recursively

```python
def generate_env_vars_recursively(data: Union[Dict, List], export_path: List[str]) -> Dict
```

Generate environment variables recursively.


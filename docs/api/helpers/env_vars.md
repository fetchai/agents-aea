<a name="aea.helpers.env_vars"></a>
# aea.helpers.env`_`vars

Implementation of the environment variables support.

<a name="aea.helpers.env_vars.is_env_variable"></a>
#### is`_`env`_`variable

```python
is_env_variable(value: Any) -> bool
```

Check is variable string with env variable pattern.

<a name="aea.helpers.env_vars.replace_with_env_var"></a>
#### replace`_`with`_`env`_`var

```python
replace_with_env_var(value: str, env_variables: dict, default_value: Any = NotSet) -> JSON_TYPES
```

Replace env var with value.

<a name="aea.helpers.env_vars.apply_env_variables"></a>
#### apply`_`env`_`variables

```python
apply_env_variables(data: Union[Dict, List[Dict]], env_variables: Mapping[str, Any], default_value: Any = NotSet) -> JSON_TYPES
```

Create new resulting dict with env variables applied.

<a name="aea.helpers.env_vars.convert_value_str_to_type"></a>
#### convert`_`value`_`str`_`to`_`type

```python
convert_value_str_to_type(value: str, type_str: str) -> JSON_TYPES
```

Convert value by type name to native python type.


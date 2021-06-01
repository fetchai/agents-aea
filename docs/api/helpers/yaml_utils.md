<a name="aea.helpers.yaml_utils"></a>
# aea.helpers.yaml`_`utils

Helper functions related to YAML loading/dumping.

<a name="aea.helpers.yaml_utils._AEAYamlLoader"></a>
## `_`AEAYamlLoader Objects

```python
class _AEAYamlLoader(yaml.SafeLoader)
```

Custom yaml.SafeLoader for the AEA framework.

It extends the default SafeLoader in two ways:
- loads YAML configurations while *remembering the order of the fields*;
- resolves the environment variables at loading time.

This class is for internal usage only; please use
the public functions of the module 'yaml_load' and 'yaml_load_all'.

<a name="aea.helpers.yaml_utils._AEAYamlLoader.__init__"></a>
#### `__`init`__`

```python
 | __init__(*args: Any, **kwargs: Any) -> None
```

Initialize the AEAYamlLoader.

It adds a YAML Loader constructor to use 'OderedDict' to load the files.

**Arguments**:

- `args`: the positional arguments.
- `kwargs`: the keyword arguments.

<a name="aea.helpers.yaml_utils._AEAYamlDumper"></a>
## `_`AEAYamlDumper Objects

```python
class _AEAYamlDumper(yaml.SafeDumper)
```

Custom yaml.SafeDumper for the AEA framework.

It extends the default SafeDumper so to dump
YAML configurations while *following the order of the fields*.

This class is for internal usage only; please use
the public functions of the module 'yaml_dump' and 'yaml_dump_all'.

<a name="aea.helpers.yaml_utils._AEAYamlDumper.__init__"></a>
#### `__`init`__`

```python
 | __init__(*args: Any, **kwargs: Any) -> None
```

Initialize the AEAYamlDumper.

It adds a YAML Dumper representer to use 'OderedDict' to dump the files.

**Arguments**:

- `args`: the positional arguments.
- `kwargs`: the keyword arguments.

<a name="aea.helpers.yaml_utils.yaml_load"></a>
#### yaml`_`load

```python
yaml_load(stream: TextIO) -> Dict[str, Any]
```

Load a yaml from a file pointer in an ordered way.

**Arguments**:

- `stream`: file pointer to the input file.

**Returns**:

the dictionary object with the YAML file content.

<a name="aea.helpers.yaml_utils.yaml_load_all"></a>
#### yaml`_`load`_`all

```python
yaml_load_all(stream: TextIO) -> List[Dict[str, Any]]
```

Load a multi-paged yaml from a file pointer in an ordered way.

**Arguments**:

- `stream`: file pointer to the input file.

**Returns**:

the list of dictionary objects with the (multi-paged) YAML file content.

<a name="aea.helpers.yaml_utils.yaml_dump"></a>
#### yaml`_`dump

```python
yaml_dump(data: Dict, stream: Optional[TextIO] = None) -> None
```

Dump YAML data to a yaml file in an ordered way.

**Arguments**:

- `data`: the data to write.
- `stream`: (optional) the file to write on.

<a name="aea.helpers.yaml_utils.yaml_dump_all"></a>
#### yaml`_`dump`_`all

```python
yaml_dump_all(data: Sequence[Dict], stream: Optional[TextIO] = None) -> None
```

Dump YAML data to a yaml file in an ordered way.

**Arguments**:

- `data`: the data to write.
- `stream`: (optional) the file to write on.


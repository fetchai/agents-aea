<a name=".aea.helpers.base"></a>
# aea.helpers.base

Miscellaneous helpers.

<a name=".aea.helpers.base.yaml_load"></a>
#### yaml`_`load

```python
yaml_load(stream: TextIO) -> Dict[str, str]
```

Load a yaml from a file pointer in an ordered way.

**Arguments**:

- `stream`: the file pointer

**Returns**:

the yaml

<a name=".aea.helpers.base.yaml_dump"></a>
#### yaml`_`dump

```python
yaml_dump(data, stream: TextIO) -> None
```

Dump data to a yaml file in an ordered way.

**Arguments**:

- `data`: the data to be dumped
- `stream`: the file pointer

<a name=".aea.helpers.base.locate"></a>
#### locate

```python
locate(path: str) -> Any
```

Locate an object by name or dotted path, importing as necessary.

<a name=".aea.helpers.base.load_aea_package"></a>
#### load`_`aea`_`package

```python
load_aea_package(configuration: ComponentConfiguration) -> None
```

Load the AEA package.

It adds all the __init__.py modules into `sys.modules`.

**Arguments**:

- `configuration`: the configuration object.

**Returns**:

None

<a name=".aea.helpers.base.load_module"></a>
#### load`_`module

```python
load_module(dotted_path: str, filepath: Path) -> types.ModuleType
```

Load a module.

**Arguments**:

- `dotted_path`: the dotted path of the package/module.
- `filepath`: the file to the package/module.

**Returns**:

None

**Raises**:

- `ValueError`: if the filepath provided is not a module.
- `Exception`: if the execution of the module raises exception.

<a name=".aea.helpers.base.load_env_file"></a>
#### load`_`env`_`file

```python
load_env_file(env_file: str)
```

Load the content of the environment file into the process environment.

**Arguments**:

- `env_file`: path to the env file.

**Returns**:

None.

<a name=".aea.helpers.base.sigint_crossplatform"></a>
#### sigint`_`crossplatform

```python
sigint_crossplatform(process: subprocess.Popen) -> None
```

Send a SIGINT, cross-platform.

The reason is because the subprocess module
doesn't have an API to send a SIGINT-like signal
both on Posix and Windows with a single method.

However, a subprocess.Popen class has the method
'send_signal' that gives more flexibility in this terms.

**Arguments**:

- `process`: the process to send the signal to.

**Returns**:

None

<a name=".aea.helpers.base.RegexConstrainedString"></a>
## RegexConstrainedString Objects

```python
class RegexConstrainedString(UserString)
```

A string that is constrained by a regex.

The default behaviour is to match anything.
Subclass this class and change the 'REGEX' class
attribute to implement a different behaviour.

<a name=".aea.helpers.base.RegexConstrainedString.__init__"></a>
#### `__`init`__`

```python
 | __init__(seq)
```

Initialize a regex constrained string.

<a name=".aea.helpers.base.cd"></a>
#### cd

```python
@contextlib.contextmanager
cd(path)
```

Change working directory temporarily.


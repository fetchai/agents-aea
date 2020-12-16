<a name="aea.helpers.base"></a>
# aea.helpers.base

Miscellaneous helpers.

<a name="aea.helpers.base.locate"></a>
#### locate

```python
locate(path: str) -> Any
```

Locate an object by name or dotted path, importing as necessary.

<a name="aea.helpers.base.load_module"></a>
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

<a name="aea.helpers.base.load_env_file"></a>
#### load`_`env`_`file

```python
load_env_file(env_file: str)
```

Load the content of the environment file into the process environment.

**Arguments**:

- `env_file`: path to the env file.

**Returns**:

None.

<a name="aea.helpers.base.sigint_crossplatform"></a>
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

<a name="aea.helpers.base.win_popen_kwargs"></a>
#### win`_`popen`_`kwargs

```python
win_popen_kwargs() -> dict
```

Return kwargs to start a process in windows with new process group.

Help to handle ctrl c properly.
Return empty dict if platform is not win32

<a name="aea.helpers.base.send_control_c"></a>
#### send`_`control`_`c

```python
send_control_c(process: subprocess.Popen, kill_group: bool = False) -> None
```

Send ctrl-C crossplatform to terminate a subprocess.

**Arguments**:

- `process`: the process to send the signal to.

**Returns**:

None

<a name="aea.helpers.base.RegexConstrainedString"></a>
## RegexConstrainedString Objects

```python
class RegexConstrainedString(UserString)
```

A string that is constrained by a regex.

The default behaviour is to match anything.
Subclass this class and change the 'REGEX' class
attribute to implement a different behaviour.

<a name="aea.helpers.base.RegexConstrainedString.__init__"></a>
#### `__`init`__`

```python
 | __init__(seq)
```

Initialize a regex constrained string.

<a name="aea.helpers.base.SimpleId"></a>
## SimpleId Objects

```python
class SimpleId(RegexConstrainedString)
```

A simple identifier.

The allowed strings are all the strings that:
- have at least length 1
- have at most length 128
- the first character must be between a-z,A-Z or underscore
- the other characters must be either the above or digits.

Examples of allowed strings:
>>> SimpleId("an_identifier")
'an_identifier'

Examples of not allowed strings:
>>> SimpleId("0an_identifier")
Traceback (most recent call last):
...
ValueError: Value 0an_identifier does not match the regular expression re.compile('[a-zA-Z_][a-zA-Z0-9_]{0,127}')

>>> SimpleId("")
Traceback (most recent call last):
...
ValueError: Value  does not match the regular expression re.compile('[a-zA-Z_][a-zA-Z0-9_]{0,127}')

<a name="aea.helpers.base.cd"></a>
#### cd

```python
@contextlib.contextmanager
cd(path)
```

Change working directory temporarily.

<a name="aea.helpers.base.get_logger_method"></a>
#### get`_`logger`_`method

```python
get_logger_method(fn: Callable, logger_method: Union[str, Callable]) -> Callable
```

Get logger method for function.

Get logger in `fn` definion module or creates logger is module.__name__.
Or return logger_method if it's callable.

**Arguments**:

- `fn`: function to get logger for.
- `logger_method`: logger name or callable.

**Returns**:

callable to write log with

<a name="aea.helpers.base.try_decorator"></a>
#### try`_`decorator

```python
try_decorator(error_message: str, default_return=None, logger_method="error")
```

Run function, log and return default value on exception.

Does not support async or coroutines!

**Arguments**:

- `error_message`: message template with one `{}` for exception
- `default_return`: value to return on exception, by default None
- `logger_method`: name of the logger method or callable to print logs

<a name="aea.helpers.base.MaxRetriesError"></a>
## MaxRetriesError Objects

```python
class MaxRetriesError(Exception)
```

Exception for retry decorator.

<a name="aea.helpers.base.retry_decorator"></a>
#### retry`_`decorator

```python
retry_decorator(number_of_retries: int, error_message: str, delay: float = 0, logger_method="error")
```

Run function with several attempts.

Does not support async or coroutines!

**Arguments**:

- `number_of_retries`: amount of attempts
- `error_message`: message template with one `{}` for exception
- `delay`: num of seconds to sleep between retries. default 0
- `logger_method`: name of the logger method or callable to print logs

<a name="aea.helpers.base.exception_log_and_reraise"></a>
#### exception`_`log`_`and`_`reraise

```python
@contextlib.contextmanager
exception_log_and_reraise(log_method: Callable, message: str)
```

Run code in context to log and re raise exception.

**Arguments**:

- `log_method`: function to print log
- `message`: message template to add error text.

<a name="aea.helpers.base.recursive_update"></a>
#### recursive`_`update

```python
recursive_update(to_update: Dict, new_values: Dict) -> None
```

Update a dictionary by replacing conflicts with the new values.

It does side-effects to the first dictionary.

>>> to_update = dict(a=1, b=2, subdict=dict(subfield1=1))
>>> new_values = dict(b=3, subdict=dict(subfield1=2))
>>> recursive_update(to_update, new_values)
>>> to_update
{'a': 1, 'b': 3, 'subdict': {'subfield1': 2}}

**Arguments**:

- `to_update`: the dictionary to update.
- `new_values`: the dictionary of new values to replace.

**Returns**:

None

<a name="aea.helpers.base.find_topological_order"></a>
#### find`_`topological`_`order

```python
find_topological_order(adjacency_list: Dict[T, Set[T]]) -> List[T]
```

Compute the topological order of a graph (using Kahn's algorithm).

**Arguments**:

- `adjacency_list`: the adjacency list of the graph.

**Returns**:

the topological order for the graph (as a sequence of nodes)

**Raises**:

- `ValueError`: if the graph contains a cycle.

<a name="aea.helpers.base.reachable_nodes"></a>
#### reachable`_`nodes

```python
reachable_nodes(adjacency_list: Dict[T, Set[T]], starting_nodes: Set[T]) -> Dict[T, Set[T]]
```

Find the reachable subgraph induced by a set of starting nodes.

**Arguments**:

- `adjacency_list`: the adjacency list of the full graph.
- `starting_nodes`: the starting nodes of the new graph.

**Returns**:

the adjacency list of the subgraph.

<a name="aea.helpers.base.cached_property"></a>
## cached`_`property Objects

```python
class cached_property()
```

Cached property from python3.8 functools.

<a name="aea.helpers.base.cached_property.__init__"></a>
#### `__`init`__`

```python
 | __init__(func)
```

Init cached property.

<a name="aea.helpers.base.cached_property.__set_name__"></a>
#### `__`set`_`name`__`

```python
 | __set_name__(_, name)
```

Set name.

<a name="aea.helpers.base.cached_property.__get__"></a>
#### `__`get`__`

```python
 | __get__(instance, _=None)
```

Get instance.

<a name="aea.helpers.base.ensure_dir"></a>
#### ensure`_`dir

```python
ensure_dir(dir_path: str) -> None
```

Check if dir_path is a directory or create it.


<a name="aea.helpers.base"></a>
# aea.helpers.base

Miscellaneous helpers.

<a name="aea.helpers.base.locate"></a>
#### locate

```python
locate(path: str) -> Any
```

Locate an object by name or dotted save_path, importing as necessary.

<a name="aea.helpers.base.load_module"></a>
#### load`_`module

```python
load_module(dotted_path: str, filepath: Path) -> types.ModuleType
```

Load a module.

**Arguments**:

- `dotted_path`: the dotted save_path of the package/module.
- `filepath`: the file to the package/module.

**Returns**:

module type

**Raises**:

- `ValueError`: if the filepath provided is not a module.  # noqa: DAR402
- `Exception`: if the execution of the module raises exception.  # noqa: DAR402

<a name="aea.helpers.base.load_env_file"></a>
#### load`_`env`_`file

```python
load_env_file(env_file: str) -> None
```

Load the content of the environment file into the process environment.

**Arguments**:

- `env_file`: save_path to the env file.

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

<a name="aea.helpers.base.win_popen_kwargs"></a>
#### win`_`popen`_`kwargs

```python
win_popen_kwargs() -> dict
```

Return kwargs to start a process in windows with new process group.

Help to handle ctrl c properly.
Return empty dict if platform is not win32

**Returns**:

windows popen kwargs

<a name="aea.helpers.base.send_control_c"></a>
#### send`_`control`_`c

```python
send_control_c(process: subprocess.Popen, kill_group: bool = False) -> None
```

Send ctrl-C cross-platform to terminate a subprocess.

**Arguments**:

- `process`: the process to send the signal to.
- `kill_group`: whether or not to kill group

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
 | __init__(seq: Union[UserString, str]) -> None
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

>>> SimpleId("an identifier")
Traceback (most recent call last):
...
ValueError: Value an identifier does not match the regular expression re.compile('[a-zA-Z_][a-zA-Z0-9_]{0,127}')

>>> SimpleId("")
Traceback (most recent call last):
...
ValueError: Value  does not match the regular expression re.compile('[a-zA-Z_][a-zA-Z0-9_]{0,127}')

<a name="aea.helpers.base.cd"></a>
#### cd

```python
@contextlib.contextmanager
cd(path: PathLike) -> Generator
```

Change working directory temporarily.

<a name="aea.helpers.base.get_logger_method"></a>
#### get`_`logger`_`method

```python
get_logger_method(fn: Callable, logger_method: Union[str, Callable]) -> Callable
```

Get logger method for function.

Get logger in `fn` definition module or creates logger is module.__name__.
Or return logger_method if it's callable.

**Arguments**:

- `fn`: function to get logger for.
- `logger_method`: logger name or callable.

**Returns**:

callable to write log with

<a name="aea.helpers.base.try_decorator"></a>
#### try`_`decorator

```python
try_decorator(error_message: str, default_return: Callable = None, logger_method: Any = "error") -> Callable
```

Run function, log and return default value on exception.

Does not support async or coroutines!

**Arguments**:

- `error_message`: message template with one `{}` for exception
- `default_return`: value to return on exception, by default None
- `logger_method`: name of the logger method or callable to print logs

**Returns**:

the callable

<a name="aea.helpers.base.MaxRetriesError"></a>
## MaxRetriesError Objects

```python
class MaxRetriesError(Exception)
```

Exception for retry decorator.

<a name="aea.helpers.base.retry_decorator"></a>
#### retry`_`decorator

```python
retry_decorator(number_of_retries: int, error_message: str, delay: float = 0, logger_method: str = "error") -> Callable
```

Run function with several attempts.

Does not support async or coroutines!

**Arguments**:

- `number_of_retries`: amount of attempts
- `error_message`: message template with one `{}` for exception
- `delay`: number of seconds to sleep between retries. default 0
- `logger_method`: name of the logger method or callable to print logs

**Returns**:

the callable

<a name="aea.helpers.base.exception_log_and_reraise"></a>
#### exception`_`log`_`and`_`reraise

```python
@contextlib.contextmanager
exception_log_and_reraise(log_method: Callable, message: str) -> Generator
```

Run code in context to log and re raise exception.

**Arguments**:

- `log_method`: function to print log
- `message`: message template to add error text.
:yield: the generator

<a name="aea.helpers.base.recursive_update"></a>
#### recursive`_`update

```python
recursive_update(to_update: Dict, new_values: Dict, allow_new_values: bool = False) -> None
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
- `allow_new_values`: whether or not to allow new values.

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
 | __init__(func: Callable) -> None
```

Init cached property.

<a name="aea.helpers.base.cached_property.__set_name__"></a>
#### `__`set`_`name`__`

```python
 | __set_name__(_: Any, name: Any) -> None
```

Set name.

<a name="aea.helpers.base.cached_property.__get__"></a>
#### `__`get`__`

```python
 | __get__(instance: Any, _: Optional[Any] = None) -> Any
```

Get instance.

<a name="aea.helpers.base.ensure_dir"></a>
#### ensure`_`dir

```python
ensure_dir(dir_path: str) -> None
```

Check if dir_path is a directory or create it.

<a name="aea.helpers.base.dict_to_path_value"></a>
#### dict`_`to`_`path`_`value

```python
dict_to_path_value(data: Mapping, path: Optional[List] = None) -> Iterable[Tuple[List[str], Any]]
```

Convert dict to sequence of terminal path build of  keys and value.

<a name="aea.helpers.base.parse_datetime_from_str"></a>
#### parse`_`datetime`_`from`_`str

```python
parse_datetime_from_str(date_string: str) -> datetime.datetime
```

Parse datetime from string.

<a name="aea.helpers.base.CertRequest"></a>
## CertRequest Objects

```python
class CertRequest()
```

Certificate request for proof of representation.

<a name="aea.helpers.base.CertRequest.__init__"></a>
#### `__`init`__`

```python
 | __init__(public_key: str, identifier: SimpleIdOrStr, ledger_id: SimpleIdOrStr, not_before: str, not_after: str, message_format: str, save_path: str) -> None
```

Initialize the certificate request.

**Arguments**:

- `public_key`: the public key, or the key id.
- `identifier`: certificate identifier.
- `ledger_id`: ledger identifier the request is referring to.
- `not_before`: specify the lower bound for certificate validity. If it is a string, it must follow the format: 'YYYY-MM-DD'. It will be interpreted as timezone UTC-0.
- `not_after`: specify the lower bound for certificate validity. If it is a string, it must follow the format: 'YYYY-MM-DD'. It will be interpreted as timezone UTC-0.
- `message_format`: message format used for signing
- `save_path`: the save_path where to save the certificate.

<a name="aea.helpers.base.CertRequest.public_key"></a>
#### public`_`key

```python
 | @property
 | public_key() -> Optional[str]
```

Get the public key.

<a name="aea.helpers.base.CertRequest.ledger_id"></a>
#### ledger`_`id

```python
 | @property
 | ledger_id() -> str
```

Get the ledger id.

<a name="aea.helpers.base.CertRequest.key_identifier"></a>
#### key`_`identifier

```python
 | @property
 | key_identifier() -> Optional[str]
```

Get the key identifier.

<a name="aea.helpers.base.CertRequest.identifier"></a>
#### identifier

```python
 | @property
 | identifier() -> str
```

Get the identifier.

<a name="aea.helpers.base.CertRequest.not_before_string"></a>
#### not`_`before`_`string

```python
 | @property
 | not_before_string() -> str
```

Get the not_before field as string.

<a name="aea.helpers.base.CertRequest.not_after_string"></a>
#### not`_`after`_`string

```python
 | @property
 | not_after_string() -> str
```

Get the not_after field as string.

<a name="aea.helpers.base.CertRequest.not_before"></a>
#### not`_`before

```python
 | @property
 | not_before() -> datetime.datetime
```

Get the not_before field.

<a name="aea.helpers.base.CertRequest.not_after"></a>
#### not`_`after

```python
 | @property
 | not_after() -> datetime.datetime
```

Get the not_after field.

<a name="aea.helpers.base.CertRequest.message_format"></a>
#### message`_`format

```python
 | @property
 | message_format() -> str
```

Get the message format.

<a name="aea.helpers.base.CertRequest.save_path"></a>
#### save`_`path

```python
 | @property
 | save_path() -> Path
```

Get the save path for the certificate.

Note: if the path is *not* absolute, then
the actual save path might depend on the context.

**Returns**:

the save path

<a name="aea.helpers.base.CertRequest.get_absolute_save_path"></a>
#### get`_`absolute`_`save`_`path

```python
 | get_absolute_save_path(path_prefix: Optional[PathLike] = None) -> Path
```

Get the absolute save path.

If save_path is an absolute path, then the prefix is ignored.
Otherwise, the path prefix is prepended.

**Arguments**:

- `path_prefix`: the (absolute) path to prepend to the save path.

**Returns**:

the actual save path.

<a name="aea.helpers.base.CertRequest.public_key_or_identifier"></a>
#### public`_`key`_`or`_`identifier

```python
 | @property
 | public_key_or_identifier() -> str
```

Get the public key or identifier.

<a name="aea.helpers.base.CertRequest.get_message"></a>
#### get`_`message

```python
 | get_message(public_key: str) -> bytes
```

Get the message to sign.

<a name="aea.helpers.base.CertRequest.construct_message"></a>
#### construct`_`message

```python
 | @classmethod
 | construct_message(cls, public_key: str, identifier: SimpleIdOrStr, not_before_string: str, not_after_string: str, message_format: str) -> bytes
```

Construct message for singning.

**Arguments**:

- `public_key`: the public key
- `identifier`: identifier to be signed
- `not_before_string`: signature not valid before
- `not_after_string`: signature not valid after
- `message_format`: message format used for signing

**Returns**:

the message

<a name="aea.helpers.base.CertRequest.get_signature"></a>
#### get`_`signature

```python
 | get_signature(path_prefix: Optional[PathLike] = None) -> str
```

Get signature from save_path.

**Arguments**:

- `path_prefix`: the path prefix to be prepended to save_path. Defaults to cwd.

**Returns**:

the signature.

<a name="aea.helpers.base.CertRequest.json"></a>
#### json

```python
 | @property
 | json() -> Dict
```

Compute the JSON representation.

<a name="aea.helpers.base.CertRequest.from_json"></a>
#### from`_`json

```python
 | @classmethod
 | from_json(cls, obj: Dict) -> "CertRequest"
```

Compute the JSON representation.

<a name="aea.helpers.base.CertRequest.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other: Any) -> bool
```

Check equality.

<a name="aea.helpers.base.compute_specifier_from_version"></a>
#### compute`_`specifier`_`from`_`version

```python
compute_specifier_from_version(version: Version) -> str
```

Compute the specifier set from a version.

version specifier is:  >=major.minor.0, <next_major.0.0

**Arguments**:

- `version`: the version

**Returns**:

the specifier set

<a name="aea.helpers.base.decorator_with_optional_params"></a>
#### decorator`_`with`_`optional`_`params

```python
decorator_with_optional_params(decorator: Callable) -> Callable
```

Make a decorator usable either with or without parameters.

In other words, if a decorator "mydecorator" is decorated with this decorator,
It can be used both as:

@mydecorator
def myfunction():
    ...

or as:

@mydecorator(arg1, kwarg1="value")
def myfunction():
    ...

**Arguments**:

- `decorator`: a decorator callable

**Returns**:

a decorator callable

<a name="aea.helpers.base.delete_directory_contents"></a>
#### delete`_`directory`_`contents

```python
delete_directory_contents(directory: Path) -> None
```

Delete the content of a directory, without deleting it.

<a name="aea.helpers.base.prepend_if_not_absolute"></a>
#### prepend`_`if`_`not`_`absolute

```python
prepend_if_not_absolute(path: PathLike, prefix: PathLike) -> PathLike
```

Prepend a path with a prefix, but only if not absolute

**Arguments**:

- `path`: the path to process.
- `prefix`: the path prefix.

**Returns**:

the same path if absolute, else the prepended path.


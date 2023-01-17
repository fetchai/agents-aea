<a id="aea.test_tools.utils"></a>

# aea.test`_`tools.utils

Helpful utilities.

<a id="aea.test_tools.utils.wait_for_condition"></a>

#### wait`_`for`_`condition

```python
def wait_for_condition(condition_checker: Callable,
                       timeout: int = 2,
                       error_msg: str = "Timeout",
                       period: float = 0.001) -> None
```

Wait for condition to occur in selected timeout.

<a id="aea.test_tools.utils.consume"></a>

#### consume

```python
def consume(iterator: Iterable) -> None
```

Consume the iterator

<a id="aea.test_tools.utils.as_context"></a>

#### as`_`context

```python
@contextmanager
def as_context(*contexts: Any) -> Generator[None, None, None]
```

Set contexts

<a id="aea.test_tools.utils.copy_class"></a>

#### copy`_`class

```python
def copy_class(cls: Type) -> Type
```

Copy a class. Useful for testing class setup configurations

<a id="aea.test_tools.utils.remove_test_directory"></a>

#### remove`_`test`_`directory

```python
def remove_test_directory(directory: Union[str, Path],
                          retries: int = 3) -> bool
```

Destroy a directory once tests are done, change permissions if needed.

Note that on Windows directories and files that are open cannot be deleted.

**Arguments**:

- `directory`: directory to be deleted
- `retries`: number of re-attempts

**Returns**:

whether the directory was successfully deleted


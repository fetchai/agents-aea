<a id="aea.manager.helpers"></a>

# aea.manager.helpers

Project helper tools.

<a id="aea.manager.helpers.AEAProject"></a>

## AEAProject Objects

```python
class AEAProject()
```

A context manager class to create and delete an AEA project.

<a id="aea.manager.helpers.AEAProject.__init__"></a>

#### `__`init`__`

```python
def __init__(name: str = "my_aea", parent_dir: Optional[str] = None)
```

Initialize an AEA project.

**Arguments**:

- `name`: the name of the AEA project.
- `parent_dir`: the parent directory.

<a id="aea.manager.helpers.AEAProject.__enter__"></a>

#### `__`enter`__`

```python
def __enter__() -> None
```

Create and enter into the project.

<a id="aea.manager.helpers.AEAProject.__exit__"></a>

#### `__`exit`__`

```python
def __exit__(exc_type, exc_val, exc_tb) -> None
```

Exit the context manager.

<a id="aea.manager.helpers.AEAProject.run_cli"></a>

#### run`_`cli

```python
@staticmethod
def run_cli(*args: Any, **kwargs: Any) -> None
```

Run a CLI command.

<a id="aea.manager.helpers.AEAProject.run_aea"></a>

#### run`_`aea

```python
@classmethod
def run_aea(cls, *args: Any, **kwargs: Any) -> None
```

Run an AEA command.

**Arguments**:

- `args`: the AEA command
- `kwargs`: keyword arguments to subprocess function


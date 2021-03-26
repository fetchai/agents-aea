<a name="aea.launcher"></a>
# aea.launcher

This module contains the implementation of multiple AEA configs launcher.

<a name="aea.launcher.load_agent"></a>
#### load`_`agent

```python
load_agent(agent_dir: Union[PathLike, str], password: Optional[str] = None) -> AEA
```

Load AEA from directory.

**Arguments**:

- `agent_dir`: agent configuration directory
- `password`: the password to encrypt/decrypt the private key.

**Returns**:

AEA instance

<a name="aea.launcher.AEADirTask"></a>
## AEADirTask Objects

```python
class AEADirTask(AbstractExecutorTask)
```

Task to run agent from agent configuration directory.

<a name="aea.launcher.AEADirTask.__init__"></a>
#### `__`init`__`

```python
 | __init__(agent_dir: Union[PathLike, str], password: Optional[str] = None) -> None
```

Init aea config dir task.

**Arguments**:

- `agent_dir`: directory with aea config.
- `password`: the password to encrypt/decrypt the private key.

<a name="aea.launcher.AEADirTask.id"></a>
#### id

```python
 | @property
 | id() -> Union[PathLike, str]
```

Return agent_dir.

<a name="aea.launcher.AEADirTask.start"></a>
#### start

```python
 | start() -> None
```

Start task.

<a name="aea.launcher.AEADirTask.stop"></a>
#### stop

```python
 | stop() -> None
```

Stop task.

<a name="aea.launcher.AEADirTask.create_async_task"></a>
#### create`_`async`_`task

```python
 | create_async_task(loop: AbstractEventLoop) -> TaskAwaitable
```

Return asyncio Task for task run in asyncio loop.

<a name="aea.launcher.AEADirMultiprocessTask"></a>
## AEADirMultiprocessTask Objects

```python
class AEADirMultiprocessTask(AbstractMultiprocessExecutorTask)
```

Task to run agent from agent configuration directory.

Version for multiprocess executor mode.

<a name="aea.launcher.AEADirMultiprocessTask.__init__"></a>
#### `__`init`__`

```python
 | __init__(agent_dir: Union[PathLike, str], log_level: Optional[str] = None, password: Optional[str] = None) -> None
```

Init aea config dir task.

**Arguments**:

- `agent_dir`: directory with aea config.
- `log_level`: debug level applied for AEA in subprocess
- `password`: the password to encrypt/decrypt the private key.

<a name="aea.launcher.AEADirMultiprocessTask.id"></a>
#### id

```python
 | @property
 | id() -> Union[PathLike, str]
```

Return agent_dir.

<a name="aea.launcher.AEADirMultiprocessTask.failed"></a>
#### failed

```python
 | @property
 | failed() -> bool
```

Return was exception failed or not.

If it's running it's not failed.

**Returns**:

bool

<a name="aea.launcher.AEADirMultiprocessTask.start"></a>
#### start

```python
 | start() -> Tuple[Callable, Sequence[Any]]
```

Return function and arguments to call within subprocess.

<a name="aea.launcher.AEADirMultiprocessTask.stop"></a>
#### stop

```python
 | stop() -> None
```

Stop task.

<a name="aea.launcher.AEALauncher"></a>
## AEALauncher Objects

```python
class AEALauncher(AbstractMultipleRunner)
```

Run multiple AEA instances.

<a name="aea.launcher.AEALauncher.__init__"></a>
#### `__`init`__`

```python
 | __init__(agent_dirs: Sequence[Union[PathLike, str]], mode: str, fail_policy: ExecutorExceptionPolicies = ExecutorExceptionPolicies.propagate, log_level: Optional[str] = None, password: Optional[str] = None) -> None
```

Init AEALauncher.

**Arguments**:

- `agent_dirs`: sequence of AEA config directories.
- `mode`: executor name to use.
- `fail_policy`: one of ExecutorExceptionPolicies to be used with Executor
- `log_level`: debug level applied for AEA in subprocesses
- `password`: the password to encrypt/decrypt the private key.


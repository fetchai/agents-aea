<a name="aea.manager.utils"></a>
# aea.manager.utils

Multiagent manager utils.

<a name="aea.manager.utils.get_lib_path"></a>
#### get`_`lib`_`path

```python
get_lib_path(env_dir: str) -> str
```

Get librarty path for env dir.

<a name="aea.manager.utils.make_venv"></a>
#### make`_`venv

```python
make_venv(env_dir: str, set_env: bool = False) -> None
```

Make venv and update variable to use it.

**Arguments**:

- `env_dir`: str, path for new env dir
- `set_env`: bool. use evn within this python process (update, sys.executable and sys.path)

<a name="aea.manager.utils.project_install_and_build"></a>
#### project`_`install`_`and`_`build

```python
project_install_and_build(project: Project) -> None
```

Install project dependencies and build required components.

<a name="aea.manager.utils.get_venv_dir_for_project"></a>
#### get`_`venv`_`dir`_`for`_`project

```python
get_venv_dir_for_project(project: Project) -> str
```

Get virtual env directory for project specified.

<a name="aea.manager.utils.project_check"></a>
#### project`_`check

```python
project_check(project: Project) -> None
```

Perform project loads well.

<a name="aea.manager.utils.run_in_venv"></a>
#### run`_`in`_`venv

```python
run_in_venv(env_dir: str, fn: Callable, timeout: float, *args: Any) -> Any
```

Run python function in a dedicated process with virtual env specified.


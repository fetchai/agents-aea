<a name="aea.helpers.install_dependency"></a>
# aea.helpers.install`_`dependency

Helper to install python dependencies.

<a name="aea.helpers.install_dependency.install_dependency"></a>
#### install`_`dependency

```python
install_dependency(dependency_name: str, dependency: Dependency, logger: Logger, install_timeout: float = 300) -> None
```

Install python dependency to the current python environment.

**Arguments**:

- `dependency_name`: name of the python package
- `dependency`: Dependency specification
- `logger`: the logger
- `install_timeout`: timeout to wait pip to install

<a name="aea.helpers.install_dependency.install_dependencies"></a>
#### install`_`dependencies

```python
install_dependencies(dependencies: List[Dependency], logger: Logger, install_timeout: float = 300) -> None
```

Install python dependencies to the current python environment.

**Arguments**:

- `dependencies`: dict of dependency name and specification
- `logger`: the logger
- `install_timeout`: timeout to wait pip to install

<a name="aea.helpers.install_dependency.call_pip"></a>
#### call`_`pip

```python
call_pip(pip_args: List[str], timeout: float = 300, retry: bool = False) -> None
```

Run pip install command.

**Arguments**:

- `pip_args`: list strings of the command
- `timeout`: timeout to wait pip to install
- `retry`: bool, try one more time if command failed

<a name="aea.helpers.install_dependency.run_install_subprocess"></a>
#### run`_`install`_`subprocess

```python
run_install_subprocess(install_command: List[str], install_timeout: float = 300) -> int
```

Try executing install command.

**Arguments**:

- `install_command`: list strings of the command
- `install_timeout`: timeout to wait pip to install

**Returns**:

the return code of the subprocess


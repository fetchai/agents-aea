<a name="aea.helpers.install_dependency"></a>
# aea.helpers.install`_`dependency

Helper to install python dependecies.

<a name="aea.helpers.install_dependency.install_dependency"></a>
#### install`_`dependency

```python
install_dependency(dependency_name: str, dependency: Dependency, logger: Logger) -> None
```

Install python dependency to the current python environment.

**Arguments**:

- `dependency_name`: name of the python package
- `dependency`: Dependency specification

**Returns**:

None

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


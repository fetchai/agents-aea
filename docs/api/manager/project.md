<a name="aea.manager.project"></a>
# aea.manager.project

This module contains the implementation of AEA agents project configuration.

<a name="aea.manager.project._Base"></a>
## `_`Base Objects

```python
class _Base()
```

Base class to share some methods.

<a name="aea.manager.project._Base.builder"></a>
#### builder

```python
 | @property
 | builder() -> AEABuilder
```

Get AEABuilder instance.

<a name="aea.manager.project._Base.install_pypi_dependencies"></a>
#### install`_`pypi`_`dependencies

```python
 | install_pypi_dependencies() -> None
```

Install python dependencies for the project.

<a name="aea.manager.project.Project"></a>
## Project Objects

```python
class Project(_Base)
```

Agent project representation.

<a name="aea.manager.project.Project.__init__"></a>
#### `__`init`__`

```python
 | __init__(public_id: PublicId, path: str) -> None
```

Init project with public_id and project's path.

<a name="aea.manager.project.Project.build"></a>
#### build

```python
 | build() -> None
```

Call all build entry points.

<a name="aea.manager.project.Project.load"></a>
#### load

```python
 | @classmethod
 | load(cls, working_dir: str, public_id: PublicId, is_local: bool = False, is_remote: bool = False, is_restore: bool = False, cli_verbosity: str = "INFO", registry_path: str = DEFAULT_REGISTRY_NAME, skip_consistency_check: bool = False, skip_aea_validation: bool = False) -> "Project"
```

Load project with given public_id to working_dir.

If local = False and remote = False, then the packages
are fetched in mixed mode (i.e. first try from local
registry, and then from remote registry in case of failure).

**Arguments**:

- `working_dir`: the working directory
- `public_id`: the public id
- `is_local`: whether to fetch from local
- `is_remote`: whether to fetch from remote
- `is_restore`: whether to restore or not
- `cli_verbosity`: the logging verbosity of the CLI
- `registry_path`: the path to the registry locally
- `skip_consistency_check`: consistency checks flag
- `skip_aea_validation`: aea validation flag

**Returns**:

project

<a name="aea.manager.project.Project.remove"></a>
#### remove

```python
 | remove() -> None
```

Remove project, do cleanup.

<a name="aea.manager.project.Project.agent_config"></a>
#### agent`_`config

```python
 | @property
 | agent_config() -> AgentConfig
```

Get the agent configuration.

<a name="aea.manager.project.Project.builder"></a>
#### builder

```python
 | @property
 | builder() -> AEABuilder
```

Get builder instance.

<a name="aea.manager.project.Project.check"></a>
#### check

```python
 | check() -> None
```

Check we can still construct an AEA from the project with builder.build.

<a name="aea.manager.project.AgentAlias"></a>
## AgentAlias Objects

```python
class AgentAlias(_Base)
```

Agent alias representation.

<a name="aea.manager.project.AgentAlias.__init__"></a>
#### `__`init`__`

```python
 | __init__(project: Project, agent_name: str, data_dir: str, password: Optional[str] = None)
```

Init agent alias with project, config, name, agent, builder.

<a name="aea.manager.project.AgentAlias.set_agent_config_from_data"></a>
#### set`_`agent`_`config`_`from`_`data

```python
 | set_agent_config_from_data(json_data: List[Dict]) -> None
```

Set agent config instance constructed from json data.

**Arguments**:

- `json_data`: agent config json data

<a name="aea.manager.project.AgentAlias.builder"></a>
#### builder

```python
 | @property
 | builder() -> AEABuilder
```

Get builder instance.

<a name="aea.manager.project.AgentAlias.agent_config"></a>
#### agent`_`config

```python
 | @property
 | agent_config() -> AgentConfig
```

Get agent config.

<a name="aea.manager.project.AgentAlias.remove_from_project"></a>
#### remove`_`from`_`project

```python
 | remove_from_project() -> None
```

Remove agent alias from project.

<a name="aea.manager.project.AgentAlias.dict"></a>
#### dict

```python
 | @property
 | dict() -> Dict[str, Any]
```

Convert AgentAlias to dict.

<a name="aea.manager.project.AgentAlias.config_json"></a>
#### config`_`json

```python
 | @property
 | config_json() -> List[Dict]
```

Get agent config json data.

<a name="aea.manager.project.AgentAlias.get_aea_instance"></a>
#### get`_`aea`_`instance

```python
 | get_aea_instance() -> AEA
```

Build new aea instance.

<a name="aea.manager.project.AgentAlias.issue_certificates"></a>
#### issue`_`certificates

```python
 | issue_certificates() -> None
```

Issue the certificates for this agent.

<a name="aea.manager.project.AgentAlias.set_overrides"></a>
#### set`_`overrides

```python
 | set_overrides(agent_overrides: Optional[Dict] = None, component_overrides: Optional[List[Dict]] = None) -> None
```

Set override for this agent alias's config.

<a name="aea.manager.project.AgentAlias.agent_config_manager"></a>
#### agent`_`config`_`manager

```python
 | @property
 | agent_config_manager() -> AgentConfigManager
```

Get agent configuration manager instance for the config.

<a name="aea.manager.project.AgentAlias.get_overridables"></a>
#### get`_`overridables

```python
 | get_overridables() -> Tuple[Dict, List[Dict]]
```

Get all overridables for this agent alias's config.

<a name="aea.manager.project.AgentAlias.get_addresses"></a>
#### get`_`addresses

```python
 | get_addresses() -> Dict[str, str]
```

Get addresses from private keys.

**Returns**:

dict with crypto id str as key and address str as value

<a name="aea.manager.project.AgentAlias.get_connections_addresses"></a>
#### get`_`connections`_`addresses

```python
 | get_connections_addresses() -> Dict[str, str]
```

Get connections addresses from connections private keys.

**Returns**:

dict with crypto id str as key and address str as value


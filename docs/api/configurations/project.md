<a name="aea.configurations.project"></a>
# aea.configurations.project

This module contains the implementation of AEA agents project configuiration.

<a name="aea.configurations.project.Project"></a>
## Project Objects

```python
class Project()
```

Agent project representation.

<a name="aea.configurations.project.Project.__init__"></a>
#### `__`init`__`

```python
 | __init__(public_id: PublicId, path: str)
```

Init project with public_id and project's path.

<a name="aea.configurations.project.Project.load"></a>
#### load

```python
 | @classmethod
 | load(cls, working_dir: str, public_id: PublicId, is_local: bool = False, is_restore: bool = False, registry_path: str = DEFAULT_REGISTRY_NAME, skip_consistency_check: bool = False) -> "Project"
```

Load project with given public_id to working_dir.

**Arguments**:

- `working_dir`: the working directory
- `public_id`: the public id
- `is_local`: whether to fetch from local or remote
- `registry_path`: the path to the registry locally
- `skip_consistency_check`: consistency checks flag

<a name="aea.configurations.project.Project.remove"></a>
#### remove

```python
 | remove() -> None
```

Remove project, do cleanup.

<a name="aea.configurations.project.AgentAlias"></a>
## AgentAlias Objects

```python
class AgentAlias()
```

Agent alias representation.

<a name="aea.configurations.project.AgentAlias.__init__"></a>
#### `__`init`__`

```python
 | __init__(project: Project, agent_name: str, config: List[Dict], agent: AEA, builder: AEABuilder)
```

Init agent alias with project, config, name, agent, builder.

<a name="aea.configurations.project.AgentAlias.remove_from_project"></a>
#### remove`_`from`_`project

```python
 | remove_from_project()
```

Remove agent alias from project.

<a name="aea.configurations.project.AgentAlias.dict"></a>
#### dict

```python
 | @property
 | dict() -> Dict[str, Any]
```

Convert AgentAlias to dict.


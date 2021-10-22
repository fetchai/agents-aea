<a name="aea.manager.manager"></a>
# aea.manager.manager

This module contains the implementation of AEA agents manager.

<a name="aea.manager.manager.ProjectNotFoundError"></a>
## ProjectNotFoundError Objects

```python
class ProjectNotFoundError(ValueError)
```

Project not found exception.

<a name="aea.manager.manager.ProjectCheckError"></a>
## ProjectCheckError Objects

```python
class ProjectCheckError(ValueError)
```

Project check error exception.

<a name="aea.manager.manager.ProjectCheckError.__init__"></a>
#### `__`init`__`

```python
 | __init__(msg: str, source_exception: Exception)
```

Init exception.

<a name="aea.manager.manager.ProjectPackageConsistencyCheckError"></a>
## ProjectPackageConsistencyCheckError Objects

```python
class ProjectPackageConsistencyCheckError(ValueError)
```

Check consistency of package versions against already added project.

<a name="aea.manager.manager.ProjectPackageConsistencyCheckError.__init__"></a>
#### `__`init`__`

```python
 | __init__(agent_project_id: PublicId, conflicting_packages: List[Tuple[PackageIdPrefix, str, str, Set[PublicId]]])
```

Initialize the exception.

**Arguments**:

- `agent_project_id`: the agent project id whose addition has failed.
- `conflicting_packages`: the conflicting packages.

<a name="aea.manager.manager.BaseAgentRunTask"></a>
## BaseAgentRunTask Objects

```python
class BaseAgentRunTask(ABC)
```

Base abstract class for agent run tasks.

<a name="aea.manager.manager.BaseAgentRunTask.start"></a>
#### start

```python
 | @abstractmethod
 | start() -> None
```

Start task.

<a name="aea.manager.manager.BaseAgentRunTask.wait"></a>
#### wait

```python
 | @abstractmethod
 | wait() -> asyncio.Future
```

Return future to wait task completed.

<a name="aea.manager.manager.BaseAgentRunTask.stop"></a>
#### stop

```python
 | @abstractmethod
 | stop() -> None
```

Stop task.

<a name="aea.manager.manager.BaseAgentRunTask.is_running"></a>
#### is`_`running

```python
 | @property
 | @abstractmethod
 | is_running() -> bool
```

Return is task running.

<a name="aea.manager.manager.AgentRunAsyncTask"></a>
## AgentRunAsyncTask Objects

```python
class AgentRunAsyncTask(BaseAgentRunTask)
```

Async task wrapper for agent.

<a name="aea.manager.manager.AgentRunAsyncTask.__init__"></a>
#### `__`init`__`

```python
 | __init__(agent: AEA, loop: asyncio.AbstractEventLoop) -> None
```

Init task with agent alias and loop.

<a name="aea.manager.manager.AgentRunAsyncTask.create_run_loop"></a>
#### create`_`run`_`loop

```python
 | create_run_loop() -> None
```

Create run loop.

<a name="aea.manager.manager.AgentRunAsyncTask.start"></a>
#### start

```python
 | start() -> None
```

Start task.

<a name="aea.manager.manager.AgentRunAsyncTask.wait"></a>
#### wait

```python
 | wait() -> asyncio.Future
```

Return future to wait task completed.

<a name="aea.manager.manager.AgentRunAsyncTask.stop"></a>
#### stop

```python
 | stop() -> None
```

Stop task.

<a name="aea.manager.manager.AgentRunAsyncTask.run"></a>
#### run

```python
 | async run() -> None
```

Run task body.

<a name="aea.manager.manager.AgentRunAsyncTask.is_running"></a>
#### is`_`running

```python
 | @property
 | is_running() -> bool
```

Return is task running.

<a name="aea.manager.manager.AgentRunThreadTask"></a>
## AgentRunThreadTask Objects

```python
class AgentRunThreadTask(AgentRunAsyncTask)
```

Threaded wrapper to run agent.

<a name="aea.manager.manager.AgentRunThreadTask.__init__"></a>
#### `__`init`__`

```python
 | __init__(agent: AEA, loop: asyncio.AbstractEventLoop) -> None
```

Init task with agent alias and loop.

<a name="aea.manager.manager.AgentRunThreadTask.create_run_loop"></a>
#### create`_`run`_`loop

```python
 | create_run_loop() -> None
```

Create run loop.

<a name="aea.manager.manager.AgentRunThreadTask.start"></a>
#### start

```python
 | start() -> None
```

Run task in a dedicated thread.

<a name="aea.manager.manager.AgentRunThreadTask.stop"></a>
#### stop

```python
 | stop() -> None
```

Stop the task.

<a name="aea.manager.manager.AgentRunProcessTask"></a>
## AgentRunProcessTask Objects

```python
class AgentRunProcessTask(BaseAgentRunTask)
```

Subprocess wrapper to run agent.

<a name="aea.manager.manager.AgentRunProcessTask.__init__"></a>
#### `__`init`__`

```python
 | __init__(agent_alias: AgentAlias, loop: asyncio.AbstractEventLoop) -> None
```

Init task with agent alias and loop.

<a name="aea.manager.manager.AgentRunProcessTask.start"></a>
#### start

```python
 | start() -> None
```

Run task in a dedicated process.

<a name="aea.manager.manager.AgentRunProcessTask.wait"></a>
#### wait

```python
 | wait() -> asyncio.Future
```

Return future to wait task completed.

<a name="aea.manager.manager.AgentRunProcessTask.stop"></a>
#### stop

```python
 | stop() -> None
```

Stop the task.

<a name="aea.manager.manager.AgentRunProcessTask.is_running"></a>
#### is`_`running

```python
 | @property
 | is_running() -> bool
```

Is agent running.

<a name="aea.manager.manager.MultiAgentManager"></a>
## MultiAgentManager Objects

```python
class MultiAgentManager()
```

Multi agents manager.

<a name="aea.manager.manager.MultiAgentManager.__init__"></a>
#### `__`init`__`

```python
 | __init__(working_dir: str, mode: str = "async", registry_path: str = DEFAULT_REGISTRY_NAME, auto_add_remove_project: bool = False, password: Optional[str] = None) -> None
```

Initialize manager.

**Arguments**:

- `working_dir`: directory to store base agents.
- `mode`: str. async or threaded
- `registry_path`: str. path to the local packages registry
- `auto_add_remove_project`: bool. add/remove project on the first agent add/last agent remove
- `password`: the password to encrypt/decrypt the private key.

<a name="aea.manager.manager.MultiAgentManager.data_dir"></a>
#### data`_`dir

```python
 | @property
 | data_dir() -> str
```

Get the certs directory.

<a name="aea.manager.manager.MultiAgentManager.get_data_dir_of_agent"></a>
#### get`_`data`_`dir`_`of`_`agent

```python
 | get_data_dir_of_agent(agent_name: str) -> str
```

Get the data directory of a specific agent.

<a name="aea.manager.manager.MultiAgentManager.is_running"></a>
#### is`_`running

```python
 | @property
 | is_running() -> bool
```

Is manager running.

<a name="aea.manager.manager.MultiAgentManager.dict_state"></a>
#### dict`_`state

```python
 | @property
 | dict_state() -> Dict[str, Any]
```

Create MultiAgentManager dist state.

<a name="aea.manager.manager.MultiAgentManager.projects"></a>
#### projects

```python
 | @property
 | projects() -> Dict[PublicId, Project]
```

Get all projects.

<a name="aea.manager.manager.MultiAgentManager.add_error_callback"></a>
#### add`_`error`_`callback

```python
 | add_error_callback(error_callback: Callable[[str, BaseException], None]) -> "MultiAgentManager"
```

Add error callback to call on error raised.

<a name="aea.manager.manager.MultiAgentManager.start_manager"></a>
#### start`_`manager

```python
 | start_manager(local: bool = False, remote: bool = False) -> "MultiAgentManager"
```

Start manager.

If local = False and remote = False, then the packages
are fetched in mixed mode (i.e. first try from local
registry, and then from remote registry in case of failure).

**Arguments**:

- `local`: whether or not to fetch from local registry.
- `remote`: whether or not to fetch from remote registry.

**Returns**:

the MultiAgentManager instance.

<a name="aea.manager.manager.MultiAgentManager.last_start_status"></a>
#### last`_`start`_`status

```python
 | @property
 | last_start_status() -> Tuple[
 |         bool, Dict[PublicId, List[Dict]], List[Tuple[PublicId, List[Dict], Exception]],
 |     ]
```

Get status of the last agents start loading state.

<a name="aea.manager.manager.MultiAgentManager.stop_manager"></a>
#### stop`_`manager

```python
 | stop_manager(cleanup: bool = True, save: bool = False) -> "MultiAgentManager"
```

Stop manager.

Stops all running agents and stop agent.

**Arguments**:

- `cleanup`: bool is cleanup on stop.
- `save`: bool is save state to file on stop.

**Returns**:

None

<a name="aea.manager.manager.MultiAgentManager.add_project"></a>
#### add`_`project

```python
 | add_project(public_id: PublicId, local: bool = False, remote: bool = False, restore: bool = False) -> "MultiAgentManager"
```

Fetch agent project and all dependencies to working_dir.

If local = False and remote = False, then the packages
are fetched in mixed mode (i.e. first try from local
registry, and then from remote registry in case of failure).

**Arguments**:

- `public_id`: the public if of the agent project.
- `local`: whether or not to fetch from local registry.
- `remote`: whether or not to fetch from remote registry.
- `restore`: bool flag for restoring already fetched agent.

**Returns**:

self

<a name="aea.manager.manager.MultiAgentManager.remove_project"></a>
#### remove`_`project

```python
 | remove_project(public_id: PublicId, keep_files: bool = False) -> "MultiAgentManager"
```

Remove agent project.

<a name="aea.manager.manager.MultiAgentManager.list_projects"></a>
#### list`_`projects

```python
 | list_projects() -> List[PublicId]
```

List all agents projects added.

**Returns**:

list of public ids of projects

<a name="aea.manager.manager.MultiAgentManager.add_agent"></a>
#### add`_`agent

```python
 | add_agent(public_id: PublicId, agent_name: Optional[str] = None, agent_overrides: Optional[dict] = None, component_overrides: Optional[List[dict]] = None, local: bool = False, remote: bool = False, restore: bool = False) -> "MultiAgentManager"
```

Create new agent configuration based on project with config overrides applied.

Alias is stored in memory only!

**Arguments**:

- `public_id`: base agent project public id
- `agent_name`: unique name for the agent
- `agent_overrides`: overrides for agent config.
- `component_overrides`: overrides for component section.
- `local`: whether or not to fetch from local registry.
- `remote`: whether or not to fetch from remote registry.
- `restore`: bool flag for restoring already fetched agent.

**Returns**:

self

<a name="aea.manager.manager.MultiAgentManager.add_agent_with_config"></a>
#### add`_`agent`_`with`_`config

```python
 | add_agent_with_config(public_id: PublicId, config: List[dict], agent_name: Optional[str] = None) -> "MultiAgentManager"
```

Create new agent configuration based on project with config provided.

Alias is stored in memory only!

**Arguments**:

- `public_id`: base agent project public id
- `agent_name`: unique name for the agent
- `config`: agent config (used for agent re-creation).

**Returns**:

manager

<a name="aea.manager.manager.MultiAgentManager.get_agent_overridables"></a>
#### get`_`agent`_`overridables

```python
 | get_agent_overridables(agent_name: str) -> Tuple[Dict, List[Dict]]
```

Get agent config  overridables.

**Arguments**:

- `agent_name`: str

**Returns**:

Tuple of agent overridables dict and  and list of component overridables dict.

<a name="aea.manager.manager.MultiAgentManager.set_agent_overrides"></a>
#### set`_`agent`_`overrides

```python
 | set_agent_overrides(agent_name: str, agent_overides: Optional[Dict], components_overrides: Optional[List[Dict]]) -> "MultiAgentManager"
```

Set agent overrides.

**Arguments**:

- `agent_name`: str
- `agent_overides`: optional dict of agent config overrides
- `components_overrides`: optional list of dict of components overrides

**Returns**:

self

<a name="aea.manager.manager.MultiAgentManager.list_agents_info"></a>
#### list`_`agents`_`info

```python
 | list_agents_info() -> List[Dict[str, Any]]
```

List agents detailed info.

**Returns**:

list of dicts that represents agent info: public_id, name, is_running.

<a name="aea.manager.manager.MultiAgentManager.list_agents"></a>
#### list`_`agents

```python
 | list_agents(running_only: bool = False) -> List[str]
```

List all agents.

**Arguments**:

- `running_only`: returns only running if set to True

**Returns**:

list of agents names

<a name="aea.manager.manager.MultiAgentManager.remove_agent"></a>
#### remove`_`agent

```python
 | remove_agent(agent_name: str, skip_project_auto_remove: bool = False) -> "MultiAgentManager"
```

Remove agent alias definition from registry.

**Arguments**:

- `agent_name`: agent name to remove
- `skip_project_auto_remove`: disable auto project remove on last agent removed.

**Returns**:

None

<a name="aea.manager.manager.MultiAgentManager.start_agent"></a>
#### start`_`agent

```python
 | start_agent(agent_name: str) -> "MultiAgentManager"
```

Start selected agent.

**Arguments**:

- `agent_name`: agent name to start

**Returns**:

None

<a name="aea.manager.manager.MultiAgentManager.start_all_agents"></a>
#### start`_`all`_`agents

```python
 | start_all_agents() -> "MultiAgentManager"
```

Start all not started agents.

**Returns**:

None

<a name="aea.manager.manager.MultiAgentManager.stop_agent"></a>
#### stop`_`agent

```python
 | stop_agent(agent_name: str) -> "MultiAgentManager"
```

Stop running agent.

**Arguments**:

- `agent_name`: agent name to stop

**Returns**:

self

<a name="aea.manager.manager.MultiAgentManager.stop_all_agents"></a>
#### stop`_`all`_`agents

```python
 | stop_all_agents() -> "MultiAgentManager"
```

Stop all agents running.

**Returns**:

self

<a name="aea.manager.manager.MultiAgentManager.stop_agents"></a>
#### stop`_`agents

```python
 | stop_agents(agent_names: List[str]) -> "MultiAgentManager"
```

Stop specified agents.

**Arguments**:

- `agent_names`: names of agents

**Returns**:

self

<a name="aea.manager.manager.MultiAgentManager.start_agents"></a>
#### start`_`agents

```python
 | start_agents(agent_names: List[str]) -> "MultiAgentManager"
```

Stop specified agents.

**Arguments**:

- `agent_names`: names of agents

**Returns**:

self

<a name="aea.manager.manager.MultiAgentManager.get_agent_alias"></a>
#### get`_`agent`_`alias

```python
 | get_agent_alias(agent_name: str) -> AgentAlias
```

Return details about agent alias definition.

**Arguments**:

- `agent_name`: name of agent

**Returns**:

AgentAlias


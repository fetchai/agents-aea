<a name="aea.manager"></a>
# aea.manager

This module contains the implementation of AEA agents manager.

<a name="aea.manager.AgentRunAsyncTask"></a>
## AgentRunAsyncTask Objects

```python
class AgentRunAsyncTask()
```

Async task wrapper for agent.

<a name="aea.manager.AgentRunAsyncTask.__init__"></a>
#### `__`init`__`

```python
 | __init__(agent: AEA, loop: asyncio.AbstractEventLoop) -> None
```

Init task with agent and loop.

<a name="aea.manager.AgentRunAsyncTask.create_run_loop"></a>
#### create`_`run`_`loop

```python
 | create_run_loop() -> None
```

Create run loop.

<a name="aea.manager.AgentRunAsyncTask.start"></a>
#### start

```python
 | start() -> None
```

Start task.

<a name="aea.manager.AgentRunAsyncTask.wait"></a>
#### wait

```python
 | wait() -> asyncio.Future
```

Return future to wait task completed.

<a name="aea.manager.AgentRunAsyncTask.stop"></a>
#### stop

```python
 | stop() -> None
```

Stop task.

<a name="aea.manager.AgentRunAsyncTask.run"></a>
#### run

```python
 | async run() -> None
```

Run task body.

<a name="aea.manager.AgentRunAsyncTask.is_running"></a>
#### is`_`running

```python
 | @property
 | is_running() -> bool
```

Return is task running.

<a name="aea.manager.AgentRunThreadTask"></a>
## AgentRunThreadTask Objects

```python
class AgentRunThreadTask(AgentRunAsyncTask)
```

Threaded wrapper to run agent.

<a name="aea.manager.AgentRunThreadTask.__init__"></a>
#### `__`init`__`

```python
 | __init__(agent: AEA, loop: asyncio.AbstractEventLoop) -> None
```

Init task with agent and loop.

<a name="aea.manager.AgentRunThreadTask.create_run_loop"></a>
#### create`_`run`_`loop

```python
 | create_run_loop() -> None
```

Create run loop.

<a name="aea.manager.AgentRunThreadTask.start"></a>
#### start

```python
 | start() -> None
```

Run task in a dedicated thread.

<a name="aea.manager.MultiAgentManager"></a>
## MultiAgentManager Objects

```python
class MultiAgentManager()
```

Multi agents manager.

<a name="aea.manager.MultiAgentManager.__init__"></a>
#### `__`init`__`

```python
 | __init__(working_dir: str, mode: str = "async", registry_path: str = "packages") -> None
```

Initialize manager.

**Arguments**:

- `working_dir`: directory to store base agents.

<a name="aea.manager.MultiAgentManager.is_running"></a>
#### is`_`running

```python
 | @property
 | is_running() -> bool
```

Is manager running.

<a name="aea.manager.MultiAgentManager.add_error_callback"></a>
#### add`_`error`_`callback

```python
 | add_error_callback(error_callback: Callable[[str, BaseException], None]) -> None
```

Add error callback to call on error raised.

<a name="aea.manager.MultiAgentManager.start_manager"></a>
#### start`_`manager

```python
 | start_manager() -> "MultiAgentManager"
```

Start manager.

<a name="aea.manager.MultiAgentManager.stop_manager"></a>
#### stop`_`manager

```python
 | stop_manager() -> "MultiAgentManager"
```

Stop manager.

Stops all running agents and stop agent.

**Returns**:

None

<a name="aea.manager.MultiAgentManager.add_project"></a>
#### add`_`project

```python
 | add_project(public_id: PublicId, local: bool = True) -> "MultiAgentManager"
```

Fetch agent project and all dependencies to working_dir.

**Arguments**:

- `public_id`: the public if of the agent project.
- `local`: whether or not to fetch from local registry.

<a name="aea.manager.MultiAgentManager.remove_project"></a>
#### remove`_`project

```python
 | remove_project(public_id: PublicId) -> "MultiAgentManager"
```

Remove agent project.

<a name="aea.manager.MultiAgentManager.list_projects"></a>
#### list`_`projects

```python
 | list_projects() -> List[PublicId]
```

List all agents projects added.

**Returns**:

lit of public ids of projects

<a name="aea.manager.MultiAgentManager.add_agent"></a>
#### add`_`agent

```python
 | add_agent(public_id: PublicId, agent_name: Optional[str] = None, agent_overrides: Optional[dict] = None, component_overrides: Optional[List[dict]] = None) -> "MultiAgentManager"
```

Create new agent configuration based on project with config overrides applied.

Alias is stored in memory only!

**Arguments**:

- `public_id`: base agent project public id
- `agent_name`: unique name for the agent
- `agent_overrides`: overrides for agent config.
- `component_overrides`: overrides for component section.

**Returns**:

manager

<a name="aea.manager.MultiAgentManager.list_agents"></a>
#### list`_`agents

```python
 | list_agents(running_only: bool = False) -> List[str]
```

List all agents.

**Arguments**:

- `running_only`: returns only running if set to True

**Returns**:

list of agents names

<a name="aea.manager.MultiAgentManager.remove_agent"></a>
#### remove`_`agent

```python
 | remove_agent(agent_name: str) -> "MultiAgentManager"
```

Remove agent alias definition from registry.

**Arguments**:

- `agent_name`: agent name to remove

**Returns**:

None

<a name="aea.manager.MultiAgentManager.start_agent"></a>
#### start`_`agent

```python
 | start_agent(agent_name: str) -> "MultiAgentManager"
```

Start selected agent.

**Arguments**:

- `agent_name`: agent name to start

**Returns**:

None

<a name="aea.manager.MultiAgentManager.start_all_agents"></a>
#### start`_`all`_`agents

```python
 | start_all_agents() -> "MultiAgentManager"
```

Start all not started agents.

**Returns**:

None

<a name="aea.manager.MultiAgentManager.stop_agent"></a>
#### stop`_`agent

```python
 | stop_agent(agent_name: str) -> "MultiAgentManager"
```

Stop running agent.

**Arguments**:

- `agent_name`: agent name to stop

**Returns**:

None

<a name="aea.manager.MultiAgentManager.stop_all_agents"></a>
#### stop`_`all`_`agents

```python
 | stop_all_agents() -> "MultiAgentManager"
```

Stop all agents running.

**Returns**:

None

<a name="aea.manager.MultiAgentManager.stop_agents"></a>
#### stop`_`agents

```python
 | stop_agents(agent_names: List[str]) -> "MultiAgentManager"
```

Stop specified agents.

**Returns**:

None

<a name="aea.manager.MultiAgentManager.start_agents"></a>
#### start`_`agents

```python
 | start_agents(agent_names: List[str]) -> "MultiAgentManager"
```

Stop specified agents.

**Returns**:

None

<a name="aea.manager.MultiAgentManager.get_agent_alias"></a>
#### get`_`agent`_`alias

```python
 | get_agent_alias(agent_name: str) -> AgentAlias
```

Return details about agent alias definition.

**Returns**:

AgentAlias

<a name="aea.manager.MultiAgentManager.install_pypi_dependencies"></a>
#### install`_`pypi`_`dependencies

```python
 | install_pypi_dependencies() -> None
```

Install dependencies for every project has at least one agent alias.


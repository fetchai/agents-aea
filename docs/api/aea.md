<a name=".aea.aea"></a>
## aea.aea

This module contains the implementation of an Autonomous Economic Agent.

<a name=".aea.aea.AEA"></a>
### AEA

```python
class AEA(Agent)
```

This class implements an autonomous economic agent.

<a name=".aea.aea.AEA.__init__"></a>
#### `__`init`__`

```python
 | __init__(identity: Identity, connections: List[Connection], wallet: Wallet, ledger_apis: LedgerApis, resources: Resources, loop: Optional[AbstractEventLoop] = None, timeout: float = 0.0, is_debug: bool = False, is_programmatic: bool = True, max_reactions: int = 20) -> None
```

Instantiate the agent.

**Arguments**:

- `identity`: the identity of the agent
- `connections`: the list of connections of the agent.
- `loop`: the event loop to run the connections.
- `wallet`: the wallet of the agent.
- `ledger_apis`: the ledger apis of the agent.
- `resources`: the resources of the agent.
- `timeout`: the time in (fractions of) seconds to time out an agent between act and react
- `is_debug`: if True, run the agent in debug mode.
- `is_programmatic`: if True, run the agent in programmatic mode (skips loading of resources from directory).
- `max_reactions`: the processing rate of messages per iteration.

**Returns**:

None

<a name=".aea.aea.AEA.decision_maker"></a>
#### decision`_`maker

```python
 | @property
 | decision_maker() -> DecisionMaker
```

Get decision maker.

<a name=".aea.aea.AEA.context"></a>
#### context

```python
 | @property
 | context() -> AgentContext
```

Get context.

<a name=".aea.aea.AEA.resources"></a>
#### resources

```python
 | @resources.setter
 | resources(resources: "Resources") -> None
```

Set resources.

<a name=".aea.aea.AEA.filter"></a>
#### filter

```python
 | @property
 | filter() -> Filter
```

Get filter.

<a name=".aea.aea.AEA.task_manager"></a>
#### task`_`manager

```python
 | @property
 | task_manager() -> TaskManager
```

Get the task manager.

<a name=".aea.aea.AEA.setup"></a>
#### setup

```python
 | setup() -> None
```

Set up the agent.

**Returns**:

None

<a name=".aea.aea.AEA.act"></a>
#### act

```python
 | act() -> None
```

Perform actions.

**Returns**:

None

<a name=".aea.aea.AEA.react"></a>
#### react

```python
 | react() -> None
```

React to incoming events (envelopes).

**Returns**:

None

<a name=".aea.aea.AEA.update"></a>
#### update

```python
 | update() -> None
```

Update the current state of the agent.

:return None

<a name=".aea.aea.AEA.teardown"></a>
#### teardown

```python
 | teardown() -> None
```

Tear down the agent.

**Returns**:

None


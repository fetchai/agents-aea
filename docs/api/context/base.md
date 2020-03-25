<a name=".aea.context.base"></a>
## aea.context.base

This module contains the agent context class.

<a name=".aea.context.base.AgentContext"></a>
### AgentContext

```python
class AgentContext()
```

Provide read access to relevant data of the agent for the skills.

<a name=".aea.context.base.AgentContext.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(identity: Identity, ledger_apis: LedgerApis, connection_status: ConnectionStatus, outbox: OutBox, decision_maker_message_queue: Queue, ownership_state: OwnershipState, preferences: Preferences, goal_pursuit_readiness: GoalPursuitReadiness, task_manager: TaskManager)
```

Initialize an agent context.

**Arguments**:

- `identity`: the identity object
- `ledger_apis`: the ledger apis
- `connection_status`: the connection status
- `outbox`: the outbox
- `decision_maker_message_queue`: the (in) queue of the decision maker
- `ownership_state`: the ownership state of the agent
- `preferences`: the preferences of the agent
- `goal_pursuit_readiness`: ready to pursuit its goals
- `task_manager`: the task manager

<a name=".aea.context.base.AgentContext.shared_state"></a>
#### shared\_state

```python
 | @property
 | shared_state() -> Dict[str, Any]
```

Get the shared state dictionary.

<a name=".aea.context.base.AgentContext.identity"></a>
#### identity

```python
 | @property
 | identity() -> Identity
```

Get the identity.

<a name=".aea.context.base.AgentContext.agent_name"></a>
#### agent\_name

```python
 | @property
 | agent_name() -> str
```

Get agent name.

<a name=".aea.context.base.AgentContext.addresses"></a>
#### addresses

```python
 | @property
 | addresses() -> Dict[str, Address]
```

Get addresses.

<a name=".aea.context.base.AgentContext.address"></a>
#### address

```python
 | @property
 | address() -> Address
```

Get the default address.

<a name=".aea.context.base.AgentContext.connection_status"></a>
#### connection\_status

```python
 | @property
 | connection_status() -> ConnectionStatus
```

Get connection status.

<a name=".aea.context.base.AgentContext.outbox"></a>
#### outbox

```python
 | @property
 | outbox() -> OutBox
```

Get outbox.

<a name=".aea.context.base.AgentContext.decision_maker_message_queue"></a>
#### decision\_maker\_message\_queue

```python
 | @property
 | decision_maker_message_queue() -> Queue
```

Get decision maker queue.

<a name=".aea.context.base.AgentContext.ownership_state"></a>
#### ownership\_state

```python
 | @property
 | ownership_state() -> OwnershipState
```

Get the ownership state of the agent.

<a name=".aea.context.base.AgentContext.preferences"></a>
#### preferences

```python
 | @property
 | preferences() -> Preferences
```

Get the preferences of the agent.

<a name=".aea.context.base.AgentContext.goal_pursuit_readiness"></a>
#### goal\_pursuit\_readiness

```python
 | @property
 | goal_pursuit_readiness() -> GoalPursuitReadiness
```

Get the goal pursuit readiness.

<a name=".aea.context.base.AgentContext.ledger_apis"></a>
#### ledger\_apis

```python
 | @property
 | ledger_apis() -> LedgerApis
```

Get the ledger APIs.

<a name=".aea.context.base.AgentContext.task_manager"></a>
#### task\_manager

```python
 | @property
 | task_manager() -> TaskManager
```

Get the task manager.

<a name=".aea.context.base.AgentContext.search_service_address"></a>
#### search\_service\_address

```python
 | @property
 | search_service_address() -> Address
```

Get the address of the search service.


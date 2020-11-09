<a name="aea.context.base"></a>
# aea.context.base

This module contains the agent context class.

<a name="aea.context.base.AgentContext"></a>
## AgentContext Objects

```python
class AgentContext()
```

Provide read access to relevant objects of the agent for the skills.

<a name="aea.context.base.AgentContext.__init__"></a>
#### `__`init`__`

```python
 | __init__(identity: Identity, connection_status: MultiplexerStatus, outbox: OutBox, decision_maker_message_queue: Queue, decision_maker_handler_context: SimpleNamespace, task_manager: TaskManager, default_ledger_id: str, currency_denominations: Dict[str, str], default_connection: Optional[PublicId], default_routing: Dict[PublicId, PublicId], search_service_address: Address, decision_maker_address: Address, **kwargs)
```

Initialize an agent context.

**Arguments**:

- `identity`: the identity object
- `connection_status`: the connection status of the multiplexer
- `outbox`: the outbox
- `decision_maker_message_queue`: the (in) queue of the decision maker
- `decision_maker_handler_context`: the decision maker's name space
- `task_manager`: the task manager
- `default_ledger_id`: the default ledger id
- `ledger_it_to_currency_denom`: mapping from ledger ids to currency denominations
- `default_connection`: the default connection
- `default_routing`: the default routing
- `search_service_address`: the address of the search service
- `decision_maker_address`: the address of the decision maker
- `kwargs`: keyword arguments to be attached in the agent context namespace.

<a name="aea.context.base.AgentContext.shared_state"></a>
#### shared`_`state

```python
 | @property
 | shared_state() -> Dict[str, Any]
```

Get the shared state dictionary.

The shared state is the only object which skills can use
to exchange state directly. It is accessible (read and write) from
all skills.

<a name="aea.context.base.AgentContext.identity"></a>
#### identity

```python
 | @property
 | identity() -> Identity
```

Get the identity.

<a name="aea.context.base.AgentContext.agent_name"></a>
#### agent`_`name

```python
 | @property
 | agent_name() -> str
```

Get agent name.

<a name="aea.context.base.AgentContext.addresses"></a>
#### addresses

```python
 | @property
 | addresses() -> Dict[str, Address]
```

Get addresses.

<a name="aea.context.base.AgentContext.address"></a>
#### address

```python
 | @property
 | address() -> Address
```

Get the default address.

<a name="aea.context.base.AgentContext.connection_status"></a>
#### connection`_`status

```python
 | @property
 | connection_status() -> MultiplexerStatus
```

Get connection status of the multiplexer.

<a name="aea.context.base.AgentContext.outbox"></a>
#### outbox

```python
 | @property
 | outbox() -> OutBox
```

Get outbox.

<a name="aea.context.base.AgentContext.decision_maker_message_queue"></a>
#### decision`_`maker`_`message`_`queue

```python
 | @property
 | decision_maker_message_queue() -> Queue
```

Get decision maker queue.

<a name="aea.context.base.AgentContext.decision_maker_handler_context"></a>
#### decision`_`maker`_`handler`_`context

```python
 | @property
 | decision_maker_handler_context() -> SimpleNamespace
```

Get the decision maker handler context.

<a name="aea.context.base.AgentContext.task_manager"></a>
#### task`_`manager

```python
 | @property
 | task_manager() -> TaskManager
```

Get the task manager.

<a name="aea.context.base.AgentContext.search_service_address"></a>
#### search`_`service`_`address

```python
 | @property
 | search_service_address() -> Address
```

Get the address of the search service.

<a name="aea.context.base.AgentContext.decision_maker_address"></a>
#### decision`_`maker`_`address

```python
 | @property
 | decision_maker_address() -> Address
```

Get the address of the decision maker.

<a name="aea.context.base.AgentContext.default_ledger_id"></a>
#### default`_`ledger`_`id

```python
 | @property
 | default_ledger_id() -> str
```

Get the default ledger id.

<a name="aea.context.base.AgentContext.currency_denominations"></a>
#### currency`_`denominations

```python
 | @property
 | currency_denominations() -> Dict[str, str]
```

Get a dictionary mapping ledger ids to currency denominations.

<a name="aea.context.base.AgentContext.default_connection"></a>
#### default`_`connection

```python
 | @property
 | default_connection() -> Optional[PublicId]
```

Get the default connection.

<a name="aea.context.base.AgentContext.default_routing"></a>
#### default`_`routing

```python
 | @property
 | default_routing() -> Dict[PublicId, PublicId]
```

Get the default routing.

<a name="aea.context.base.AgentContext.namespace"></a>
#### namespace

```python
 | @property
 | namespace() -> SimpleNamespace
```

Get the agent context namespace.


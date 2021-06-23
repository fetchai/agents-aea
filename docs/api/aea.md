<a name="aea.aea"></a>
# aea.aea

This module contains the implementation of an autonomous economic agent (AEA).

<a name="aea.aea.AEA"></a>
## AEA Objects

```python
class AEA(Agent)
```

This class implements an autonomous economic agent.

<a name="aea.aea.AEA.__init__"></a>
#### `__`init`__`

```python
 | __init__(identity: Identity, wallet: Wallet, resources: Resources, data_dir: str, loop: Optional[AbstractEventLoop] = None, period: float = 0.05, execution_timeout: float = 0, max_reactions: int = 20, error_handler_class: Optional[Type[AbstractErrorHandler]] = None, error_handler_config: Optional[Dict[str, Any]] = None, decision_maker_handler_class: Optional[Type[DecisionMakerHandler]] = None, decision_maker_handler_config: Optional[Dict[str, Any]] = None, skill_exception_policy: ExceptionPolicyEnum = ExceptionPolicyEnum.propagate, connection_exception_policy: ExceptionPolicyEnum = ExceptionPolicyEnum.propagate, loop_mode: Optional[str] = None, runtime_mode: Optional[str] = None, default_ledger: Optional[str] = None, currency_denominations: Optional[Dict[str, str]] = None, default_connection: Optional[PublicId] = None, default_routing: Optional[Dict[PublicId, PublicId]] = None, connection_ids: Optional[Collection[PublicId]] = None, search_service_address: str = DEFAULT_SEARCH_SERVICE_ADDRESS, storage_uri: Optional[str] = None, task_manager_mode: Optional[str] = None, **kwargs: Any, ,) -> None
```

Instantiate the agent.

**Arguments**:

- `identity`: the identity of the agent
- `wallet`: the wallet of the agent.
- `resources`: the resources (protocols and skills) of the agent.
- `data_dir`: directory where to put local files.
- `loop`: the event loop to run the connections.
- `period`: period to call agent's act
- `execution_timeout`: amount of time to limit single act/handle to execute.
- `max_reactions`: the processing rate of envelopes per tick (i.e. single loop).
- `error_handler_class`: the class implementing the error handler
- `error_handler_config`: the configuration of the error handler
- `decision_maker_handler_class`: the class implementing the decision maker handler to be used.
- `decision_maker_handler_config`: the configuration of the decision maker handler
- `skill_exception_policy`: the skill exception policy enum
- `connection_exception_policy`: the connection exception policy enum
- `loop_mode`: loop_mode to choose agent run loop.
- `runtime_mode`: runtime mode (async, threaded) to run AEA in.
- `default_ledger`: default ledger id
- `currency_denominations`: mapping from ledger id to currency denomination
- `default_connection`: public id to the default connection
- `default_routing`: dictionary for default routing.
- `connection_ids`: active connection ids. Default: consider all the ones in the resources.
- `search_service_address`: the address of the search service used.
- `storage_uri`: optional uri to set generic storage
- `task_manager_mode`: task manager mode (threaded) to run tasks with.
- `kwargs`: keyword arguments to be attached in the agent context namespace.

<a name="aea.aea.AEA.get_build_dir"></a>
#### get`_`build`_`dir

```python
 | @classmethod
 | get_build_dir(cls) -> str
```

Get agent build directory.

<a name="aea.aea.AEA.context"></a>
#### context

```python
 | @property
 | context() -> AgentContext
```

Get (agent) context.

<a name="aea.aea.AEA.resources"></a>
#### resources

```python
 | @property
 | resources() -> Resources
```

Get resources.

<a name="aea.aea.AEA.resources"></a>
#### resources

```python
 | @resources.setter
 | resources(resources: "Resources") -> None
```

Set resources.

<a name="aea.aea.AEA.filter"></a>
#### filter

```python
 | @property
 | filter() -> Filter
```

Get the filter.

<a name="aea.aea.AEA.active_behaviours"></a>
#### active`_`behaviours

```python
 | @property
 | active_behaviours() -> List[Behaviour]
```

Get all active behaviours to use in act.

<a name="aea.aea.AEA.setup"></a>
#### setup

```python
 | setup() -> None
```

Set up the agent.

Calls setup() on the resources.

<a name="aea.aea.AEA.act"></a>
#### act

```python
 | act() -> None
```

Perform actions.

Adds new handlers and behaviours for use/execution by the runtime.

<a name="aea.aea.AEA.handle_envelope"></a>
#### handle`_`envelope

```python
 | handle_envelope(envelope: Envelope) -> None
```

Handle an envelope.

Performs the following:

- fetching the protocol referenced by the envelope, and
- handling if the protocol is unsupported, using the error handler, or
- handling if there is a decoding error, using the error handler, or
- handling if no active handler is available for the specified protocol, using the error handler, or
- handling the message recovered from the envelope with all active handlers for the specified protocol.

**Arguments**:

- `envelope`: the envelope to handle.

**Returns**:

None

<a name="aea.aea.AEA.get_periodic_tasks"></a>
#### get`_`periodic`_`tasks

```python
 | get_periodic_tasks() -> Dict[Callable, Tuple[float, Optional[datetime.datetime]]]
```

Get all periodic tasks for agent.

**Returns**:

dict of callable with period specified

<a name="aea.aea.AEA.get_message_handlers"></a>
#### get`_`message`_`handlers

```python
 | get_message_handlers() -> List[Tuple[Callable[[Any], None], Callable]]
```

Get handlers with message getters.

**Returns**:

List of tuples of callables: handler and coroutine to get a message

<a name="aea.aea.AEA.exception_handler"></a>
#### exception`_`handler

```python
 | exception_handler(exception: Exception, function: Callable) -> bool
```

Handle exception raised during agent main loop execution.

**Arguments**:

- `exception`: exception raised
- `function`: a callable exception raised in.

**Returns**:

bool, propagate exception if True otherwise skip it.

<a name="aea.aea.AEA.teardown"></a>
#### teardown

```python
 | teardown() -> None
```

Tear down the agent.

Performs the following:

- tears down the resources.

<a name="aea.aea.AEA.get_task_result"></a>
#### get`_`task`_`result

```python
 | get_task_result(task_id: int) -> AsyncResult
```

Get the result from a task.

**Arguments**:

- `task_id`: the id of the task

**Returns**:

async result for task_id

<a name="aea.aea.AEA.enqueue_task"></a>
#### enqueue`_`task

```python
 | enqueue_task(func: Callable, args: Sequence = (), kwargs: Optional[Dict[str, Any]] = None) -> int
```

Enqueue a task with the task manager.

**Arguments**:

- `func`: the callable instance to be enqueued
- `args`: the positional arguments to be passed to the function.
- `kwargs`: the keyword arguments to be passed to the function.

**Returns**:

the task id to get the the result.


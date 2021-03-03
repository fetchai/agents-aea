<a name="aea.abstract_agent"></a>
# aea.abstract`_`agent

This module contains the interface definition of the abstract agent.

<a name="aea.abstract_agent.AbstractAgent"></a>
## AbstractAgent Objects

```python
class AbstractAgent(ABC)
```

This class provides an abstract base  interface for an agent.

<a name="aea.abstract_agent.AbstractAgent.name"></a>
#### name

```python
 | @abstractproperty
 | name() -> str
```

Get agent's name.

<a name="aea.abstract_agent.AbstractAgent.storage_uri"></a>
#### storage`_`uri

```python
 | @abstractproperty
 | storage_uri() -> Optional[str]
```

Return storage uri.

<a name="aea.abstract_agent.AbstractAgent.start"></a>
#### start

```python
 | @abstractmethod
 | start() -> None
```

Start the agent.

**Returns**:

None

<a name="aea.abstract_agent.AbstractAgent.stop"></a>
#### stop

```python
 | @abstractmethod
 | stop() -> None
```

Stop the agent.

**Returns**:

None

<a name="aea.abstract_agent.AbstractAgent.setup"></a>
#### setup

```python
 | @abstractmethod
 | setup() -> None
```

Set up the agent.

**Returns**:

None

<a name="aea.abstract_agent.AbstractAgent.act"></a>
#### act

```python
 | @abstractmethod
 | act() -> None
```

Perform actions on period.

**Returns**:

None

<a name="aea.abstract_agent.AbstractAgent.handle_envelope"></a>
#### handle`_`envelope

```python
 | @abstractmethod
 | handle_envelope(envelope: Envelope) -> None
```

Handle an envelope.

**Arguments**:

- `envelope`: the envelope to handle.

**Returns**:

None

<a name="aea.abstract_agent.AbstractAgent.get_periodic_tasks"></a>
#### get`_`periodic`_`tasks

```python
 | @abstractmethod
 | get_periodic_tasks() -> Dict[Callable, Tuple[float, Optional[datetime.datetime]]]
```

Get all periodic tasks for agent.

**Returns**:

dict of callable with period specified

<a name="aea.abstract_agent.AbstractAgent.get_message_handlers"></a>
#### get`_`message`_`handlers

```python
 | @abstractmethod
 | get_message_handlers() -> List[Tuple[Callable[[Any], None], Callable]]
```

Get handlers with message getters.

**Returns**:

List of tuples of callables: handler and coroutine to get a message

<a name="aea.abstract_agent.AbstractAgent.exception_handler"></a>
#### exception`_`handler

```python
 | @abstractmethod
 | exception_handler(exception: Exception, function: Callable) -> Optional[bool]
```

Handle exception raised during agent main loop execution.

**Arguments**:

- `exception`: exception raised
- `function`: a callable exception raised in.

**Returns**:

skip exception if True, otherwise re-raise it

<a name="aea.abstract_agent.AbstractAgent.teardown"></a>
#### teardown

```python
 | @abstractmethod
 | teardown() -> None
```

Tear down the agent.

**Returns**:

None


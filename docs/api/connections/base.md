<a name=".aea.connections.base"></a>
## aea.connections.base

The base connection package.

<a name=".aea.connections.base.ConnectionStatus"></a>
### ConnectionStatus

```python
class ConnectionStatus()
```

The connection status class.

<a name=".aea.connections.base.ConnectionStatus.__init__"></a>
#### `__`init`__`

```python
 | __init__()
```

Initialize the connection status.

<a name=".aea.connections.base.Connection"></a>
### Connection

```python
class Connection(ABC)
```

Abstract definition of a connection.

<a name=".aea.connections.base.Connection.__init__"></a>
#### `__`init`__`

```python
 | __init__(connection_id: Optional[PublicId] = None, restricted_to_protocols: Optional[Set[PublicId]] = None, excluded_protocols: Optional[Set[PublicId]] = None)
```

Initialize the connection.

**Arguments**:

- `connection_id`: the connection identifier.
- `restricted_to_protocols`: the set of protocols ids of the only supported protocols for this connection.
- `excluded_protocols`: the set of protocols ids that we want to exclude for this connection.

<a name=".aea.connections.base.Connection.loop"></a>
#### loop

```python
 | @loop.setter
 | loop(loop: AbstractEventLoop) -> None
```

Set the event loop.

**Arguments**:

- `loop`: the event loop.

**Returns**:

None

<a name=".aea.connections.base.Connection.connection_id"></a>
#### connection`_`id

```python
 | @property
 | connection_id() -> PublicId
```

Get the id of the connection.

<a name=".aea.connections.base.Connection.restricted_to_protocols"></a>
#### restricted`_`to`_`protocols

```python
 | @property
 | restricted_to_protocols() -> Set[PublicId]
```

Get the restricted to protocols..

<a name=".aea.connections.base.Connection.excluded_protocols"></a>
#### excluded`_`protocols

```python
 | @property
 | excluded_protocols() -> Set[PublicId]
```

Get the restricted to protocols..

<a name=".aea.connections.base.Connection.connection_status"></a>
#### connection`_`status

```python
 | @property
 | connection_status() -> ConnectionStatus
```

Get the connection status.

<a name=".aea.connections.base.Connection.connect"></a>
#### connect

```python
 | @abstractmethod
 | async connect()
```

Set up the connection.

<a name=".aea.connections.base.Connection.disconnect"></a>
#### disconnect

```python
 | @abstractmethod
 | async disconnect()
```

Tear down the connection.

<a name=".aea.connections.base.Connection.send"></a>
#### send

```python
 | @abstractmethod
 | async send(envelope: "Envelope") -> None
```

Send an envelope.

**Arguments**:

- `envelope`: the envelope to send.

**Returns**:

None

<a name=".aea.connections.base.Connection.receive"></a>
#### receive

```python
 | @abstractmethod
 | async receive(*args, **kwargs) -> Optional["Envelope"]
```

Receive an envelope.

**Returns**:

the received envelope, or None if an error occurred.

<a name=".aea.connections.base.Connection.from_config"></a>
#### from`_`config

```python
 | @classmethod
 | @abstractmethod
 | from_config(cls, address: "Address", connection_configuration: ConnectionConfig) -> "Connection"
```

Initialize a connection instance from a configuration.

**Arguments**:

- `address`: the address of the agent.
- `connection_configuration`: the connection configuration.

**Returns**:

an instance of the concrete connection class.


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
class Connection(Component,  ABC)
```

Abstract definition of a connection.

<a name=".aea.connections.base.Connection.__init__"></a>
#### `__`init`__`

```python
 | __init__(configuration: Optional[ConnectionConfig] = None, address: Optional["Address"] = None, restricted_to_protocols: Optional[Set[PublicId]] = None, excluded_protocols: Optional[Set[PublicId]] = None, connection_id: Optional[PublicId] = None)
```

Initialize the connection.

The configuration must be specified if and only if the following
parameters are None: connection_id, excluded_protocols or restricted_to_protocols.

**Arguments**:

- `configuration`: the connection configuration.
- `address`: the address.
- `restricted_to_protocols`: the set of protocols ids of the only supported protocols for this connection.
- `excluded_protocols`: the set of protocols ids that we want to exclude for this connection.
- `connection_id`: the connection identifier.

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

<a name=".aea.connections.base.Connection.address"></a>
#### address

```python
 | @address.setter
 | address(address: "Address") -> None
```

Set the address to be used by the connection.

**Arguments**:

- `address`: a public key.

**Returns**:

None

<a name=".aea.connections.base.Connection.component_type"></a>
#### component`_`type

```python
 | @property
 | component_type() -> ComponentType
```

Get the component type.

<a name=".aea.connections.base.Connection.connection_id"></a>
#### connection`_`id

```python
 | @property
 | connection_id() -> PublicId
```

Get the id of the connection.

<a name=".aea.connections.base.Connection.configuration"></a>
#### configuration

```python
 | @property
 | configuration() -> ConnectionConfig
```

Get the connection configuration.

<a name=".aea.connections.base.Connection.excluded_protocols"></a>
#### excluded`_`protocols

```python
 | @property
 | excluded_protocols() -> Set[PublicId]
```

Get the ids of the excluded protocols for this connection.

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
 | from_config(cls, address: "Address", configuration: ConnectionConfig) -> "Connection"
```

Initialize a connection instance from a configuration.

**Arguments**:

- `address`: the address of the agent.
- `configuration`: the connection configuration.

**Returns**:

an instance of the concrete connection class.


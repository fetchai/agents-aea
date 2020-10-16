<a name="aea.connections.base"></a>
# aea.connections.base

The base connection package.

<a name="aea.connections.base.ConnectionStates"></a>
## ConnectionStates Objects

```python
class ConnectionStates(Enum)
```

Connection states enum.

<a name="aea.connections.base.Connection"></a>
## Connection Objects

```python
class Connection(Component,  ABC)
```

Abstract definition of a connection.

<a name="aea.connections.base.Connection.__init__"></a>
#### `__`init`__`

```python
 | __init__(configuration: ConnectionConfig, identity: Optional[Identity] = None, crypto_store: Optional[CryptoStore] = None, restricted_to_protocols: Optional[Set[PublicId]] = None, excluded_protocols: Optional[Set[PublicId]] = None, **kwargs, ,)
```

Initialize the connection.

The configuration must be specified if and only if the following
parameters are None: connection_id, excluded_protocols or restricted_to_protocols.

**Arguments**:

- `configuration`: the connection configuration.
- `identity`: the identity object held by the agent.
- `crypto_store`: the crypto store for encrypted communication.
- `restricted_to_protocols`: the set of protocols ids of the only supported protocols for this connection.
- `excluded_protocols`: the set of protocols ids that we want to exclude for this connection.

<a name="aea.connections.base.Connection.loop"></a>
#### loop

```python
 | @property
 | loop() -> asyncio.AbstractEventLoop
```

Get the event loop.

<a name="aea.connections.base.Connection.address"></a>
#### address

```python
 | @property
 | address() -> "Address"
```

Get the address.

<a name="aea.connections.base.Connection.crypto_store"></a>
#### crypto`_`store

```python
 | @property
 | crypto_store() -> CryptoStore
```

Get the crypto store.

<a name="aea.connections.base.Connection.has_crypto_store"></a>
#### has`_`crypto`_`store

```python
 | @property
 | has_crypto_store() -> bool
```

Check if the connection has the crypto store.

<a name="aea.connections.base.Connection.component_type"></a>
#### component`_`type

```python
 | @property
 | component_type() -> ComponentType
```

Get the component type.

<a name="aea.connections.base.Connection.configuration"></a>
#### configuration

```python
 | @property
 | configuration() -> ConnectionConfig
```

Get the connection configuration.

<a name="aea.connections.base.Connection.restricted_to_protocols"></a>
#### restricted`_`to`_`protocols

```python
 | @property
 | restricted_to_protocols() -> Set[PublicId]
```

Get the ids of the protocols this connection is restricted to.

<a name="aea.connections.base.Connection.excluded_protocols"></a>
#### excluded`_`protocols

```python
 | @property
 | excluded_protocols() -> Set[PublicId]
```

Get the ids of the excluded protocols for this connection.

<a name="aea.connections.base.Connection.state"></a>
#### state

```python
 | @property
 | state() -> ConnectionStates
```

Get the connection status.

<a name="aea.connections.base.Connection.connect"></a>
#### connect

```python
 | @abstractmethod
 | async connect()
```

Set up the connection.

<a name="aea.connections.base.Connection.disconnect"></a>
#### disconnect

```python
 | @abstractmethod
 | async disconnect()
```

Tear down the connection.

<a name="aea.connections.base.Connection.send"></a>
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

<a name="aea.connections.base.Connection.receive"></a>
#### receive

```python
 | @abstractmethod
 | async receive(*args, **kwargs) -> Optional["Envelope"]
```

Receive an envelope.

**Returns**:

the received envelope, or None if an error occurred.

<a name="aea.connections.base.Connection.from_dir"></a>
#### from`_`dir

```python
 | @classmethod
 | from_dir(cls, directory: str, identity: Identity, crypto_store: CryptoStore, **kwargs) -> "Connection"
```

Load the connection from a directory.

**Arguments**:

- `directory`: the directory to the connection package.
- `identity`: the identity object.
- `crypto_store`: object to access the connection crypto objects.

**Returns**:

the connection object.

<a name="aea.connections.base.Connection.from_config"></a>
#### from`_`config

```python
 | @classmethod
 | from_config(cls, configuration: ConnectionConfig, identity: Identity, crypto_store: CryptoStore, **kwargs, ,) -> "Connection"
```

Load a connection from a configuration.

**Arguments**:

- `configuration`: the connection configuration.
- `identity`: the identity object.
- `crypto_store`: object to access the connection crypto objects.

**Returns**:

an instance of the concrete connection class.

<a name="aea.connections.base.Connection.is_connected"></a>
#### is`_`connected

```python
 | @property
 | is_connected() -> bool
```

Return is connected state.

<a name="aea.connections.base.Connection.is_connecting"></a>
#### is`_`connecting

```python
 | @property
 | is_connecting() -> bool
```

Return is connecting state.

<a name="aea.connections.base.Connection.is_disconnected"></a>
#### is`_`disconnected

```python
 | @property
 | is_disconnected() -> bool
```

Return is disconnected state.


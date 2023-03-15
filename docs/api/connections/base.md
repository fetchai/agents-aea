<a id="aea.connections.base"></a>

# aea.connections.base

The base connection package.

<a id="aea.connections.base.ConnectionStates"></a>

## ConnectionStates Objects

```python
class ConnectionStates(Enum)
```

Connection states enum.

<a id="aea.connections.base.Connection"></a>

## Connection Objects

```python
class Connection(Component, ABC)
```

Abstract definition of a connection.

<a id="aea.connections.base.Connection.connection_id"></a>

#### connection`_`id

type: PublicId

<a id="aea.connections.base.Connection.__init__"></a>

#### `__`init`__`

```python
def __init__(configuration: ConnectionConfig,
             data_dir: str,
             identity: Optional[Identity] = None,
             crypto_store: Optional[CryptoStore] = None,
             restricted_to_protocols: Optional[Set[PublicId]] = None,
             excluded_protocols: Optional[Set[PublicId]] = None,
             **kwargs: Any) -> None
```

Initialize the connection.

The configuration must be specified if and only if the following
parameters are None: connection_id, excluded_protocols or restricted_to_protocols.

**Arguments**:

- `configuration`: the connection configuration.
- `data_dir`: directory where to put local files.
- `identity`: the identity object held by the agent.
- `crypto_store`: the crypto store for encrypted communication.
- `restricted_to_protocols`: the set of protocols ids of the only supported protocols for this connection.
- `excluded_protocols`: the set of protocols ids that we want to exclude for this connection.
- `kwargs`: keyword arguments passed to component base

<a id="aea.connections.base.Connection.loop"></a>

#### loop

```python
@property
def loop() -> asyncio.AbstractEventLoop
```

Get the event loop.

<a id="aea.connections.base.Connection.address"></a>

#### address

```python
@property
def address() -> "Address"
```

Get the address.

<a id="aea.connections.base.Connection.crypto_store"></a>

#### crypto`_`store

```python
@property
def crypto_store() -> CryptoStore
```

Get the crypto store.

<a id="aea.connections.base.Connection.has_crypto_store"></a>

#### has`_`crypto`_`store

```python
@property
def has_crypto_store() -> bool
```

Check if the connection has the crypto store.

<a id="aea.connections.base.Connection.data_dir"></a>

#### data`_`dir

```python
@property
def data_dir() -> str
```

Get the data directory.

<a id="aea.connections.base.Connection.component_type"></a>

#### component`_`type

```python
@property
def component_type() -> ComponentType
```

Get the component type.

<a id="aea.connections.base.Connection.configuration"></a>

#### configuration

```python
@property
def configuration() -> ConnectionConfig
```

Get the connection configuration.

<a id="aea.connections.base.Connection.restricted_to_protocols"></a>

#### restricted`_`to`_`protocols

```python
@property
def restricted_to_protocols() -> Set[PublicId]
```

Get the ids of the protocols this connection is restricted to.

<a id="aea.connections.base.Connection.excluded_protocols"></a>

#### excluded`_`protocols

```python
@property
def excluded_protocols() -> Set[PublicId]
```

Get the ids of the excluded protocols for this connection.

<a id="aea.connections.base.Connection.state"></a>

#### state

```python
@property
def state() -> ConnectionStates
```

Get the connection status.

<a id="aea.connections.base.Connection.state"></a>

#### state

```python
@state.setter
def state(value: ConnectionStates) -> None
```

Set the connection status.

<a id="aea.connections.base.Connection.connect"></a>

#### connect

```python
@abstractmethod
async def connect() -> None
```

Set up the connection.

<a id="aea.connections.base.Connection.disconnect"></a>

#### disconnect

```python
@abstractmethod
async def disconnect() -> None
```

Tear down the connection.

<a id="aea.connections.base.Connection.send"></a>

#### send

```python
@abstractmethod
async def send(envelope: "Envelope") -> None
```

Send an envelope.

**Arguments**:

- `envelope`: the envelope to send.

**Returns**:

None

<a id="aea.connections.base.Connection.receive"></a>

#### receive

```python
@abstractmethod
async def receive(*args: Any, **kwargs: Any) -> Optional["Envelope"]
```

Receive an envelope.

**Arguments**:

- `args`: positional arguments
- `kwargs`: keyword arguments

**Returns**:

the received envelope, or None if an error occurred.

<a id="aea.connections.base.Connection.from_dir"></a>

#### from`_`dir

```python
@classmethod
def from_dir(cls, directory: str, identity: Identity,
             crypto_store: CryptoStore, data_dir: str,
             **kwargs: Any) -> "Connection"
```

Load the connection from a directory.

**Arguments**:

- `directory`: the directory to the connection package.
- `identity`: the identity object.
- `crypto_store`: object to access the connection crypto objects.
- `data_dir`: the assets directory.
- `kwargs`: keyword arguments passed to connection base

**Returns**:

the connection object.

<a id="aea.connections.base.Connection.from_config"></a>

#### from`_`config

```python
@classmethod
def from_config(cls, configuration: ConnectionConfig, identity: Identity,
                crypto_store: CryptoStore, data_dir: str,
                **kwargs: Any) -> "Connection"
```

Load a connection from a configuration.

**Arguments**:

- `configuration`: the connection configuration.
- `identity`: the identity object.
- `crypto_store`: object to access the connection crypto objects.
- `data_dir`: the directory of the AEA project data.
- `kwargs`: keyword arguments passed to component base

**Returns**:

an instance of the concrete connection class.

<a id="aea.connections.base.Connection.is_connected"></a>

#### is`_`connected

```python
@property
def is_connected() -> bool
```

Return is connected state.

<a id="aea.connections.base.Connection.is_connecting"></a>

#### is`_`connecting

```python
@property
def is_connecting() -> bool
```

Return is connecting state.

<a id="aea.connections.base.Connection.is_disconnected"></a>

#### is`_`disconnected

```python
@property
def is_disconnected() -> bool
```

Return is disconnected state.

<a id="aea.connections.base.BaseSyncConnection"></a>

## BaseSyncConnection Objects

```python
class BaseSyncConnection(Connection)
```

Base sync connection class to write connections with sync code.

<a id="aea.connections.base.BaseSyncConnection.__init__"></a>

#### `__`init`__`

```python
def __init__(configuration: ConnectionConfig,
             data_dir: str,
             identity: Optional[Identity] = None,
             crypto_store: Optional[CryptoStore] = None,
             restricted_to_protocols: Optional[Set[PublicId]] = None,
             excluded_protocols: Optional[Set[PublicId]] = None,
             **kwargs: Any) -> None
```

Initialize the connection.

The configuration must be specified if and only if the following
parameters are None: connection_id, excluded_protocols or restricted_to_protocols.

**Arguments**:

- `configuration`: the connection configuration.
- `data_dir`: directory where to put local files.
- `identity`: the identity object held by the agent.
- `crypto_store`: the crypto store for encrypted communication.
- `restricted_to_protocols`: the set of protocols ids of the only supported protocols for this connection.
- `excluded_protocols`: the set of protocols ids that we want to exclude for this connection.
- `kwargs`: keyword arguments passed to connection base

<a id="aea.connections.base.BaseSyncConnection.put_envelope"></a>

#### put`_`envelope

```python
def put_envelope(envelope: Optional["Envelope"]) -> None
```

Put envelope in to the incoming queue.

<a id="aea.connections.base.BaseSyncConnection.connect"></a>

#### connect

```python
async def connect() -> None
```

Connect connection.

<a id="aea.connections.base.BaseSyncConnection.disconnect"></a>

#### disconnect

```python
async def disconnect() -> None
```

Disconnect connection.

<a id="aea.connections.base.BaseSyncConnection.send"></a>

#### send

```python
async def send(envelope: "Envelope") -> None
```

Send envelope to connection.

<a id="aea.connections.base.BaseSyncConnection.receive"></a>

#### receive

```python
async def receive(*args: Any, **kwargs: Any) -> Optional["Envelope"]
```

Get an envelope from the connection.

<a id="aea.connections.base.BaseSyncConnection.start_main"></a>

#### start`_`main

```python
def start_main() -> None
```

Start main function of the connection.

<a id="aea.connections.base.BaseSyncConnection.main"></a>

#### main

```python
def main() -> None
```

Run main body of the connection in dedicated thread.

<a id="aea.connections.base.BaseSyncConnection.on_connect"></a>

#### on`_`connect

```python
@abstractmethod
def on_connect() -> None
```

Run on connect method called.

<a id="aea.connections.base.BaseSyncConnection.on_disconnect"></a>

#### on`_`disconnect

```python
@abstractmethod
def on_disconnect() -> None
```

Run on disconnect method called.

<a id="aea.connections.base.BaseSyncConnection.on_send"></a>

#### on`_`send

```python
@abstractmethod
def on_send(envelope: "Envelope") -> None
```

Run on send method called.


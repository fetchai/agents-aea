<a name=".aea.connections.stub.connection"></a>
## aea.connections.stub.connection

This module contains the stub connection.

<a name=".aea.connections.stub.connection.lock_file"></a>
#### lock`_`file

```python
@contextmanager
lock_file(file_descriptor: IO[AnyStr])
```

Lock file in context manager.

**Arguments**:

- `file_descriptor`: file descriptio of file to lock.

<a name=".aea.connections.stub.connection.StubConnection.__init__"></a>
#### `__`init`__`

```python
 | __init__(input_file_path: Union[str, Path], output_file_path: Union[str, Path], **kwargs)
```

Initialize a stub connection.

**Arguments**:

- `input_file_path`: the input file for the incoming messages.
- `output_file_path`: the output file for the outgoing messages.

<a name=".aea.connections.stub.connection.StubConnection.read_envelopes"></a>
#### read`_`envelopes

```python
 | read_envelopes() -> None
```

Receive new envelopes, if any.

<a name=".aea.connections.stub.connection.StubConnection.receive"></a>
#### receive

```python
 | async receive(*args, **kwargs) -> Optional["Envelope"]
```

Receive an envelope.

<a name=".aea.connections.stub.connection.StubConnection.connect"></a>
#### connect

```python
 | async connect() -> None
```

Set up the connection.

<a name=".aea.connections.stub.connection.StubConnection.disconnect"></a>
#### disconnect

```python
 | async disconnect() -> None
```

Disconnect from the channel.

In this type of connection there's no channel to disconnect.

<a name=".aea.connections.stub.connection.StubConnection.send"></a>
#### send

```python
 | async send(envelope: Envelope)
```

Send messages.

**Returns**:

None

<a name=".aea.connections.stub.connection.StubConnection.from_config"></a>
#### from`_`config

```python
 | @classmethod
 | from_config(cls, address: Address, configuration: ConnectionConfig) -> "Connection"
```

Get the stub connection from the connection configuration.

**Arguments**:

- `address`: the address of the agent.
- `configuration`: the connection configuration object.

**Returns**:

the connection object


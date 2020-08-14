<a name="aea.connections.stub.connection"></a>
# aea.connections.stub.connection

This module contains the stub connection.

<a name="aea.connections.stub.connection.lock_file"></a>
#### lock`_`file

```python
@contextmanager
lock_file(file_descriptor: IO[bytes])
```

Lock file in context manager.

**Arguments**:

- `file_descriptor`: file descriptio of file to lock.

<a name="aea.connections.stub.connection.write_envelope"></a>
#### write`_`envelope

```python
write_envelope(envelope: Envelope, file_pointer: IO[bytes]) -> None
```

Write envelope to file.

<a name="aea.connections.stub.connection.write_with_lock"></a>
#### write`_`with`_`lock

```python
write_with_lock(file_pointer: IO[bytes], data: Union[bytes]) -> None
```

Write bytes to file protected with file lock.

<a name="aea.connections.stub.connection.StubConnection"></a>
## StubConnection Objects

```python
class StubConnection(Connection)
```

<a name="aea.connections.stub.connection.StubConnection.__init__"></a>
#### `__`init`__`

```python
 | __init__(**kwargs)
```

Initialize a stub connection.

<a name="aea.connections.stub.connection.StubConnection.read_envelopes"></a>
#### read`_`envelopes

```python
 | async read_envelopes() -> None
```

Read envelopes from inptut file, decode and put into in_queue.

<a name="aea.connections.stub.connection.StubConnection.receive"></a>
#### receive

```python
 | async receive(*args, **kwargs) -> Optional["Envelope"]
```

Receive an envelope.

<a name="aea.connections.stub.connection.StubConnection.connect"></a>
#### connect

```python
 | async connect() -> None
```

Set up the connection.

<a name="aea.connections.stub.connection.StubConnection.disconnect"></a>
#### disconnect

```python
 | async disconnect() -> None
```

Disconnect from the channel.

In this type of connection there's no channel to disconnect.

<a name="aea.connections.stub.connection.StubConnection.send"></a>
#### send

```python
 | async send(envelope: Envelope) -> None
```

Send messages.

**Returns**:

None


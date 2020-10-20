<a name="packages.fetchai.connections.stub.connection"></a>
# packages.fetchai.connections.stub.connection

This module contains the stub connection.

<a name="packages.fetchai.connections.stub.connection.StubConnection"></a>
## StubConnection Objects

```python
class StubConnection(Connection)
```

<a name="packages.fetchai.connections.stub.connection.StubConnection.__init__"></a>
#### `__`init`__`

```python
 | __init__(**kwargs)
```

Initialize a stub connection.

<a name="packages.fetchai.connections.stub.connection.StubConnection.read_envelopes"></a>
#### read`_`envelopes

```python
 | async read_envelopes() -> None
```

Read envelopes from inptut file, decode and put into in_queue.

<a name="packages.fetchai.connections.stub.connection.StubConnection.receive"></a>
#### receive

```python
 | async receive(*args, **kwargs) -> Optional["Envelope"]
```

Receive an envelope.

<a name="packages.fetchai.connections.stub.connection.StubConnection.connect"></a>
#### connect

```python
 | async connect() -> None
```

Set up the connection.

<a name="packages.fetchai.connections.stub.connection.StubConnection.disconnect"></a>
#### disconnect

```python
 | async disconnect() -> None
```

Disconnect from the channel.

In this type of connection there's no channel to disconnect.

<a name="packages.fetchai.connections.stub.connection.StubConnection.send"></a>
#### send

```python
 | async send(envelope: Envelope) -> None
```

Send messages.

**Returns**:

None


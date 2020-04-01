<a name=".aea.connections.stub.connection"></a>
## aea.connections.stub.connection

This module contains the stub connection.

<a name=".aea.connections.stub.connection.StubConnection.load"></a>
#### load

```python
 | load()
```

Set the connection up.

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


<a name="aea.helpers.pipe"></a>
# aea.helpers.pipe

Portable pipe implementation for Linux, MacOS, and Windows.

<a name="aea.helpers.pipe.IPCChannelClient"></a>
## IPCChannelClient Objects

```python
class IPCChannelClient(ABC)
```

Multi-platform interprocess communication channel for the client side.

<a name="aea.helpers.pipe.IPCChannelClient.connect"></a>
#### connect

```python
 | @abstractmethod
 | async connect(timeout: float = PIPE_CONN_TIMEOUT) -> bool
```

Connect to communication channel

**Arguments**:

- `timeout`: timeout for other end to connect

**Returns**:

connection status

<a name="aea.helpers.pipe.IPCChannelClient.write"></a>
#### write

```python
 | @abstractmethod
 | async write(data: bytes) -> None
```

Write `data` bytes to the other end of the channel

Will first write the size than the actual data

**Arguments**:

- `data`: bytes to write

<a name="aea.helpers.pipe.IPCChannelClient.read"></a>
#### read

```python
 | @abstractmethod
 | async read() -> Optional[bytes]
```

Read bytes from the other end of the channel

Will first read the size than the actual data

**Returns**:

read bytes

<a name="aea.helpers.pipe.IPCChannelClient.close"></a>
#### close

```python
 | @abstractmethod
 | async close() -> None
```

Close the communication channel.

<a name="aea.helpers.pipe.IPCChannel"></a>
## IPCChannel Objects

```python
class IPCChannel(IPCChannelClient)
```

Multi-platform interprocess communication channel.

<a name="aea.helpers.pipe.IPCChannel.in_path"></a>
#### in`_`path

```python
 | @property
 | @abstractmethod
 | in_path() -> str
```

Rendezvous point for incoming communication.

**Returns**:

path

<a name="aea.helpers.pipe.IPCChannel.out_path"></a>
#### out`_`path

```python
 | @property
 | @abstractmethod
 | out_path() -> str
```

Rendezvous point for outgoing communication.

**Returns**:

path

<a name="aea.helpers.pipe.PosixNamedPipeProtocol"></a>
## PosixNamedPipeProtocol Objects

```python
class PosixNamedPipeProtocol()
```

Posix named pipes async wrapper communication protocol.

<a name="aea.helpers.pipe.PosixNamedPipeProtocol.__init__"></a>
#### `__`init`__`

```python
 | __init__(in_path: str, out_path: str, logger: logging.Logger = _default_logger, loop: Optional[AbstractEventLoop] = None) -> None
```

Initialize a new posix named pipe.

**Arguments**:

- `in_path`: rendezvous point for incoming data
- `out_path`: rendezvous point for outgoing data
- `logger`: the logger
- `loop`: the event loop

<a name="aea.helpers.pipe.PosixNamedPipeProtocol.connect"></a>
#### connect

```python
 | async connect(timeout: float = PIPE_CONN_TIMEOUT) -> bool
```

Connect to the other end of the pipe

**Arguments**:

- `timeout`: timeout before failing

**Returns**:

connection success

<a name="aea.helpers.pipe.PosixNamedPipeProtocol.write"></a>
#### write

```python
 | async write(data: bytes) -> None
```

Write to pipe.

**Arguments**:

- `data`: bytes to write to pipe

<a name="aea.helpers.pipe.PosixNamedPipeProtocol.read"></a>
#### read

```python
 | async read() -> Optional[bytes]
```

Read from pipe.

**Returns**:

read bytes

<a name="aea.helpers.pipe.PosixNamedPipeProtocol.close"></a>
#### close

```python
 | async close() -> None
```

Disconnect pipe.

<a name="aea.helpers.pipe.TCPSocketProtocol"></a>
## TCPSocketProtocol Objects

```python
class TCPSocketProtocol()
```

TCP socket communication protocol.

<a name="aea.helpers.pipe.TCPSocketProtocol.__init__"></a>
#### `__`init`__`

```python
 | __init__(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, logger: logging.Logger = _default_logger, loop: Optional[AbstractEventLoop] = None) -> None
```

Initialize the tcp socket protocol.

**Arguments**:

- `reader`: established asyncio reader
- `writer`: established asyncio writer
- `logger`: the logger
- `loop`: the event loop

<a name="aea.helpers.pipe.TCPSocketProtocol.writer"></a>
#### writer

```python
 | @property
 | writer() -> StreamWriter
```

Get a writer associated with  protocol.

<a name="aea.helpers.pipe.TCPSocketProtocol.write"></a>
#### write

```python
 | async write(data: bytes) -> None
```

Write to socket.

**Arguments**:

- `data`: bytes to write

<a name="aea.helpers.pipe.TCPSocketProtocol.read"></a>
#### read

```python
 | async read() -> Optional[bytes]
```

Read from socket.

**Returns**:

read bytes

<a name="aea.helpers.pipe.TCPSocketProtocol.close"></a>
#### close

```python
 | async close() -> None
```

Disconnect socket.

<a name="aea.helpers.pipe.TCPSocketChannel"></a>
## TCPSocketChannel Objects

```python
class TCPSocketChannel(IPCChannel)
```

Interprocess communication channel implementation using tcp sockets.

<a name="aea.helpers.pipe.TCPSocketChannel.__init__"></a>
#### `__`init`__`

```python
 | __init__(logger: logging.Logger = _default_logger, loop: Optional[AbstractEventLoop] = None) -> None
```

Initialize tcp socket interprocess communication channel.

<a name="aea.helpers.pipe.TCPSocketChannel.connect"></a>
#### connect

```python
 | async connect(timeout: float = PIPE_CONN_TIMEOUT) -> bool
```

Setup communication channel and wait for other end to connect.

**Arguments**:

- `timeout`: timeout for the connection to be established

**Returns**:

connection status

<a name="aea.helpers.pipe.TCPSocketChannel.write"></a>
#### write

```python
 | async write(data: bytes) -> None
```

Write to channel.

**Arguments**:

- `data`: bytes to write

<a name="aea.helpers.pipe.TCPSocketChannel.read"></a>
#### read

```python
 | async read() -> Optional[bytes]
```

Read from channel.

**Returns**:

read bytes

<a name="aea.helpers.pipe.TCPSocketChannel.close"></a>
#### close

```python
 | async close() -> None
```

Disconnect from channel and clean it up.

<a name="aea.helpers.pipe.TCPSocketChannel.in_path"></a>
#### in`_`path

```python
 | @property
 | in_path() -> str
```

Rendezvous point for incoming communication.

<a name="aea.helpers.pipe.TCPSocketChannel.out_path"></a>
#### out`_`path

```python
 | @property
 | out_path() -> str
```

Rendezvous point for outgoing communication.

<a name="aea.helpers.pipe.PosixNamedPipeChannel"></a>
## PosixNamedPipeChannel Objects

```python
class PosixNamedPipeChannel(IPCChannel)
```

Interprocess communication channel implementation using Posix named pipes.

<a name="aea.helpers.pipe.PosixNamedPipeChannel.__init__"></a>
#### `__`init`__`

```python
 | __init__(logger: logging.Logger = _default_logger, loop: Optional[AbstractEventLoop] = None) -> None
```

Initialize posix named pipe interprocess communication channel.

<a name="aea.helpers.pipe.PosixNamedPipeChannel.connect"></a>
#### connect

```python
 | async connect(timeout: float = PIPE_CONN_TIMEOUT) -> bool
```

Setup communication channel and wait for other end to connect.

**Arguments**:

- `timeout`: timeout for connection to be established

**Returns**:

bool, indicating success

<a name="aea.helpers.pipe.PosixNamedPipeChannel.write"></a>
#### write

```python
 | async write(data: bytes) -> None
```

Write to the channel.

**Arguments**:

- `data`: data to write to channel

<a name="aea.helpers.pipe.PosixNamedPipeChannel.read"></a>
#### read

```python
 | async read() -> Optional[bytes]
```

Read from the channel.

**Returns**:

read bytes

<a name="aea.helpers.pipe.PosixNamedPipeChannel.close"></a>
#### close

```python
 | async close() -> None
```

Close the channel and clean it up.

<a name="aea.helpers.pipe.PosixNamedPipeChannel.in_path"></a>
#### in`_`path

```python
 | @property
 | in_path() -> str
```

Rendezvous point for incoming communication.

<a name="aea.helpers.pipe.PosixNamedPipeChannel.out_path"></a>
#### out`_`path

```python
 | @property
 | out_path() -> str
```

Rendezvous point for outgoing communication.

<a name="aea.helpers.pipe.TCPSocketChannelClient"></a>
## TCPSocketChannelClient Objects

```python
class TCPSocketChannelClient(IPCChannelClient)
```

Interprocess communication channel client using tcp sockets.

<a name="aea.helpers.pipe.TCPSocketChannelClient.__init__"></a>
#### `__`init`__`

```python
 | __init__(in_path: str, out_path: str, logger: logging.Logger = _default_logger, loop: Optional[AbstractEventLoop] = None) -> None
```

Initialize a tcp socket communication channel client.

**Arguments**:

- `in_path`: rendezvous point for incoming data
- `out_path`: rendezvous point for outgoing data
- `logger`: the logger
- `loop`: the event loop

<a name="aea.helpers.pipe.TCPSocketChannelClient.connect"></a>
#### connect

```python
 | async connect(timeout: float = PIPE_CONN_TIMEOUT) -> bool
```

Connect to the other end of the communication channel.

**Arguments**:

- `timeout`: timeout for connection to be established

**Returns**:

connection status

<a name="aea.helpers.pipe.TCPSocketChannelClient.write"></a>
#### write

```python
 | async write(data: bytes) -> None
```

Write data to channel.

**Arguments**:

- `data`: bytes to write

<a name="aea.helpers.pipe.TCPSocketChannelClient.read"></a>
#### read

```python
 | async read() -> Optional[bytes]
```

Read data from channel.

**Returns**:

read bytes

<a name="aea.helpers.pipe.TCPSocketChannelClient.close"></a>
#### close

```python
 | async close() -> None
```

Disconnect from communication channel.

<a name="aea.helpers.pipe.PosixNamedPipeChannelClient"></a>
## PosixNamedPipeChannelClient Objects

```python
class PosixNamedPipeChannelClient(IPCChannelClient)
```

Interprocess communication channel client using Posix named pipes.

<a name="aea.helpers.pipe.PosixNamedPipeChannelClient.__init__"></a>
#### `__`init`__`

```python
 | __init__(in_path: str, out_path: str, logger: logging.Logger = _default_logger, loop: Optional[AbstractEventLoop] = None) -> None
```

Initialize a posix named pipe communication channel client.

**Arguments**:

- `in_path`: rendezvous point for incoming data
- `out_path`: rendezvous point for outgoing data
- `logger`: the logger
- `loop`: the event loop

<a name="aea.helpers.pipe.PosixNamedPipeChannelClient.connect"></a>
#### connect

```python
 | async connect(timeout: float = PIPE_CONN_TIMEOUT) -> bool
```

Connect to the other end of the communication channel.

**Arguments**:

- `timeout`: timeout for connection to be established

**Returns**:

connection status

<a name="aea.helpers.pipe.PosixNamedPipeChannelClient.write"></a>
#### write

```python
 | async write(data: bytes) -> None
```

Write data to channel.

**Arguments**:

- `data`: bytes to write

<a name="aea.helpers.pipe.PosixNamedPipeChannelClient.read"></a>
#### read

```python
 | async read() -> Optional[bytes]
```

Read data from channel.

**Returns**:

read bytes

<a name="aea.helpers.pipe.PosixNamedPipeChannelClient.close"></a>
#### close

```python
 | async close() -> None
```

Disconnect from communication channel.

<a name="aea.helpers.pipe.make_ipc_channel"></a>
#### make`_`ipc`_`channel

```python
make_ipc_channel(logger: logging.Logger = _default_logger, loop: Optional[AbstractEventLoop] = None) -> IPCChannel
```

Build a portable bidirectional InterProcess Communication channel

**Arguments**:

- `logger`: the logger
- `loop`: the loop

**Returns**:

IPCChannel

<a name="aea.helpers.pipe.make_ipc_channel_client"></a>
#### make`_`ipc`_`channel`_`client

```python
make_ipc_channel_client(in_path: str, out_path: str, logger: logging.Logger = _default_logger, loop: Optional[AbstractEventLoop] = None) -> IPCChannelClient
```

Build a portable bidirectional InterProcess Communication client channel

**Arguments**:

- `in_path`: rendezvous point for incoming communication
- `out_path`: rendezvous point for outgoing outgoing
- `logger`: the logger
- `loop`: the loop

**Returns**:

IPCChannel


A <a href="../api/connections/base#connection-objects">`Connection`</a> provides an interface for the agent to connect with entities in the outside world. Connections wrap SDKs or APIs and provide interfaces to networks, ledgers and other services. As such, a connection is concerned with I/O bound and continuously connected operations. Where necessary, a connection is responsible for translating between the framework specific <a href="../protocol">protocol</a> (an <a href="../api/mail/base#envelope-objects">`Envelope`</a> with its contained <a href="../api/protocols/base#message-objects">`Message`</a>) and the external service or third-party protocol (e.g. `HTTP`). Hence, there are two roles for connections: wrapper and transport connection. The transport connection is responsible to delivering AEA envelopes.

The messages constructed or received by a connection are eventually processed by one or several <a href="../skill">skills</a> which deal with handling and generating messages related to a specific business objective.

<img src="../assets/multiplexer.png" alt="Multiplexer of an AEA" class="center" style="display: block; margin-left: auto; margin-right: auto;width:50%;">

An `AEA` can interact with multiple connections at the same time via the <a href="../api/connections/base#connection-objects">`Multiplexer`</a>. Connections are passive in terms of multiplexer interactions (its methods are called by the Multiplexer), but they can run their own asynchronous or threaded tasks.

The `Multiplexer` maintains an <a href="../api/multiplexer#inbox-objects">`InBox`</a> and <a href="../api/multiplexer#outbox-objects">`OutBox`</a>, which are, respectively, queues for incoming and outgoing envelopes and their contained messages.

## Developing your connection

The easiest way to get started developing your own connection is by using the <a href="../scaffolding">scaffold</a> command:

``` bash
aea scaffold connection my_new_connection
```

This will scaffold a connection package called `my_new_connection` with three files:

* `__init__.py` 
* `connection.py` containing the scaffolded connection class
* `connection.yaml` containing the scaffolded configuration file

As a developer you have the choice between implementing a sync or asynchronous interface. The scaffolded `connection.py` file contains two classes: the `MyScaffoldAsyncConnection` inherited from the <a href="../api/connections/base#connection-objects">`Connection`</a> base class and the `MyScaffoldSyncConnection` inherited from the <a href="../api/connections/base#connection-objects">`BaseSyncConnection`</a>. Remove the unused class.

### Primary methods to develop - asynchronous connection interface

The developer needs to implement four public coroutines:

- The `connect` coroutine implements the setup logic required to be performed for the connection when it is initially launched. The `connect` coroutine is called by the AEA framework once when the agent is being started.

- The `disconnect` coroutine implements the teardown logic required to be performed for the connection when it is eventually stopped. The `disconnect` coroutine is called by the AEA framework once when the agent is being stopped.

- The `send` coroutine is called by the AEA framework each time the `Multiplexer` handles an outgoing envelope specified to be handled by this connection. The `send` coroutine must implement the processing of the envelope leaving the agent.

- The `receive` coroutine is continuously called by the AEA framework. It either returns `None` or an envelope. The `receive` coroutine must implement the logic of data being received by the agent, and if necessary, its translation into a relevant protocol.

The framework provides a demo `stub` connection which implements an I/O reader and writer to send and receive messages between the agent and a local file. To gain inspiration and become familiar with the structure of connection packages, you may find it useful to check out `fetchai/stub:0.21.0`, `fetchai/http_server:0.22.0` or `fetchai/http_client:0.23.0` connections. The latter two connections are for external clients to connect with an agent, and for the agent to connect with external servers, respectively.

### Primary methods to develop - sync connection interface

The <a href="../api/connections/base#connection-objects">`BaseSyncConnection`</a> uses executors to execute synchronous code from the asynchronous context of the `Multiplexer` in executors/threads, which are limited by the amount of configured workers.

The asynchronous methods `connect`, `disconnect` and `send` are converted to callbacks which the developer implements:
* `on_connect`
* `on_disconnect`
* `on_send`

All of these methods will be executed in the executor pool.

Every method can create a message by putting it into the thread/asynchronous friendly queue that is consumed by the `Multiplexer`.

The `receive` coroutine has no direct equivalent. Instead, the developer implements a `main` method which runs synchronously in the background.

## Configuration

Every connection must have a configuration file in `connection.yaml`, containing meta-information about the connection as well as all the required configuration details. For more details, have a look <a href="../config">here</a>.

### Configuration options

The `connection.yaml` file contains a number of fields that must be edited by the developer of the connection:

``` yaml
connections: []
protocols: []
class_name: MyScaffoldConnection
config:
  foo: bar
excluded_protocols: []
restricted_to_protocols: []
dependencies: {}
is_abstract: false
cert_requests: []
```

- `connections` specifies the list of other connection this connection depends on
- `protocols` specifies the list of protocols this connection depends on
- `class_name` needs to match the name of the connection class in `connection.py`
- `config` can contain arbitrary configuration information which is made available in the constructor of the connection as keyword arguments (`**kwargs`)
- `excluded_protocols` lists the protocols which cannot be used in this connection
- `restricted_to_protocols` lists the protocols which this connection is restricted to be used by
- `dependencies` lists any Python dependencies of the connection package
- `is_abstract` specifies whether this connection is only used as an abstract base class
- `cert_requests` lists certification requests of the connection (see <a href="../por">proof of representation</a> for details)

<br />

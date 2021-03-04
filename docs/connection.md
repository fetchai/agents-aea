A <a href="../api/connections/base#connection-objects">`Connection`</a> wraps an SDK or API and provides an interface to network, ledgers and other services. As such a connection is concerned with I/O bound and continuously connected operations. Where necessary, a connection is responsible for translating between the framework specific <a href="../protocol">protocol</a> (an <a href="../api/mail/base#envelope-objects">`Envelope`</a> with its contained <a href="../api/protocols/base#message-objects">`Message`</a>) and the external service or third-party protocol (e.g. `HTTP`).

The messages constructed or received by a connection are eventually processed by one or several <a href="../skill">skills</a> which deal with handling and generating messages related to a specific business objective.

The framework provides one default connection, called `stub`. It implements an I/O reader and writer to send messages to the agent from a local file. Additional connections can be added as packages.

An `AEA` can interact with multiple connections at the same time via the <a href="../api/connections/base#connection-objects">`Multiplexer`</a>.

<img src="../assets/multiplexer.png" alt="Multiplexer of an AEA" class="center" style="display: block; margin-left: auto; margin-right: auto;width:50%;">

It maintains an <a href="../api/multiplexer#inbox-objects">`InBox`</a> and <a href="../api/multiplexer#outbox-objects">`OutBox`</a>, which are, respectively, queues for incoming and outgoing envelopes and their contained messages.

## Configuration

The `connection.yaml` file of a connection package contains meta information on the connection as well as all the required configuration details. For more details have a look <a href="../config">here</a>

## Developing your own

The easiest way to get started developing your own connection is by using the <a href="../scaffolding">scaffold</a> command:

``` bash
aea scaffold connection my_new_connection
```

This will scaffold a connection package called `my_new_connection` with three files:

* `__init__.py` 
* `connection.py`, containing the scaffolded connection class
* `connection.yaml`, containing the scaffolded configuration file

### Primary methods to develop

The scaffolded `connection.py` file contains a single class inherited from the <a href="../api/connections/base#connection-objects">`Connection`</a> base class.

The developer needs to implement four public coroutines:

- The `connect` coroutine implements the setup logic required to be performed for the connection when it is initially launched. The `connect` coroutine is called by the AEA framework once when the agent is being started.

- The `disconnect` coroutine implements the teardown logic required to be performed for the connection when it is eventually stopped. The `disconnect` coroutine is called by the AEA framework once when the agent is being stopped.

- The `send` coroutine is called by the AEA framework each time when the `Multiplexer` handles an outgoing envelope specified to be handled by the connection. The `send` coroutine must implement the processing of the envelope leaving the agent.

- The `receive` coroutine is continuously called by the AEA framework. It either returns `None` or an envelope. The `receive` coroutine must implement the logic of data being received by the agent and if necessary its translation into a relevant protocol.


When developing your own connection you might benefit from inspecting the `fetchai/http_server:0.17.0` and `fetchai/http_client:0.18.0` connections to gain more familiarity and inspiration.

### Configuration options

The `connection.yaml` files contains a number of fields required to be edited by the developer of the connection:

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
- `config` can contain arbitrary configuration information which is available in the constructor of the connection
- `excluded_protocols` lists the protocols which cannot be used in this connection
- `restricted_to_protocols` lists the protocols which this connection is restricted to be used by
- `dependencies` lists any Python dependencies of the package
- `is_abstract` specifies whether this connection is only used as an abstract base class
- `cert_requests` lists certification requests of the connection (see <a href="../por">proof of representation</a> for details)

<br />

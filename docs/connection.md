A <a href="../api/connections/base#connection-objects">`Connection`</a> wraps an SDK or API and provides an interface to network, ledgers and other services. Where necessary, a connection is responsible for translating between the framework specific <a href="../api/mail/base#envelope-objects">`Envelope`</a>  with its contained <a href="../api/protocols/base#message-objects">`Message`</a> and the external service or third-party protocol (e.g. `HTTP`).

The framework provides one default connection, called `stub`. It implements an I/O reader and writer to send messages to the agent from a local file. Additional connections can be added as packages.

An `AEA` can interact with multiple connections at the same time via the <a href="../api/connections/base#connection-objects">`Multiplexer`</a>.

<img src="/assets/multiplexer.png" alt="Multiplexer of an AEA" class="center" style="display: block; margin-left: auto; margin-right: auto;width:50%;">

It maintains an <a href="../api/multiplexer#inbox-objects">`InBox`</a> and <a href="../api/multiplexer#outbox-objects">`OutBox`</a>, which are, respectively, queues for incoming and outgoing envelopes.

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
* `connection.yaml` containing the scaffolded configuration file

<br />





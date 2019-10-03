A `Connection` is attached to a `MailBox` within the AEA framework.

The `connection.py` module in the `connections` directory contains two classes. A `Connection` object has a reference to a `Channel`. 

* `Channel`: a wrapper for an SDK or API.
* `Connection`: a proxy to the functionality of an SDK or API.


## Configuration

The `connection.yaml` file in the agent directory contains protocol details and connection url and port details. For example, the oef `connection.yaml` contains the connection class name, supported protocols, and any connection configuration details.

``` json
name: oef
authors: Fetch.AI Limited
version: 0.1.0
license: Apache 2.0
url: ""
class_name: OEFConnection
supported_protocols: ["oef"]
config:
  addr: 127.0.0.1
  port: 10000

```


The developer is left to implement the methods of both `Connection` and `Channel` classes dependent on the protocol type. 

<!--We'll demonstrate implementations from the `oef` connection as an example.-->


## `Channel`


### `send(self, envelope: Envelope) `
<!--
``` python
def send(self, envelope: Envelope) -> None:
    if envelope.protocol_id == "default":
      	self.send_default_message(envelope)
   	elif envelope.protocol_id == "fipa":
       	self.send_fipa_message(envelope)
   	elif envelope.protocol_id == "oef":
       	self.send_oef_message(envelope)
   	elif envelope.protocol_id == "tac":
      	self.send_default_message(envelope)
   	else:
    	logger.error("This envelope cannot be sent: protocol_id={}".format(envelope.protocol_id))
        raise ValueError("Cannot send message.")
```
-->
### `connect(self) -> Optional[Queue]`
<!--
`Channel.connect() not implemented in oef`
-->
### `disconnect(self)`
<!--
`Channel.disconnect() not implemented in oef`
-->

## `Connection`

### `is_established(self)`
<!--
``` python
@property
def is_established(self) -> bool:
    return self._connected
```
-->
### `connect(self)`
<!--
``` python
def connect(self) -> None:
 	if self._stopped and not self._connected:
    	self._stopped = False
        self._core.run_threaded()
        try:
        	if not self.channel.connect():
            	raise ConnectionError("Cannot connect to OEFChannel.")
            self._connected = True
            self.out_thread = Thread(target=self._fetch)
            self.out_thread.start()
      	except ConnectionError as e:
            self._core.stop()
            raise e
```
-->
### `disconnect(self)`
<!--
``` python
def disconnect(self) -> None:
assert self.out_thread is not None, "Call connect before disconnect."
    if not self._stopped and self._connected:
       	self._connected = False
        self.out_thread.join()
        self.out_thread = None
        self.channel.disconnect()
        self._core.stop()
        self._stopped = True
```
-->
### `send(self, envelope: Envelope)`
<!--
``` python
def send(self, envelope: Envelope):
    if self._connected:
    	self.channel.send(envelope)
```
-->
### `from_config(cls, public_key: str, connection_configuration: ConnectionConfig)`
<!--
``` python
@classmethod
   	def from_config(cls, public_key: str, connection_configuration: ConnectionConfig) -> 'Connection':
        oef_addr = cast(str, connection_configuration.config.get("addr"))
        oef_port = cast(int, connection_configuration.config.get("port"))
        return OEFConnection(public_key, oef_addr, oef_port)
```
-->



## Envelope

An `Envelope` wraps messages. It travels from `OutBox` to agent and back to `InBox` in the `MailBox` via a protocol connection.

Construct an `Envelope` object with the `to`, `sender`, `protocol_id`, and `message` parameters.
<!--
``` python
def __init__(self, to: Address, sender: Address, protocol_id: ProtocolId, message: bytes):
        """
        Initialize a Message object.
        :param to: the public key of the receiver.
        :param sender: the public key of the sender.
        :param protocol_id: the protocol id.
        :param message: the protocol-specific message
        """
        self._to = to
        self._sender = sender
        self._protocol_id = protocol_id
        self._message = message
```
-->

<br />




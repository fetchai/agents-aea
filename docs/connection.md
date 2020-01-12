A `Connection` is attached to an `AEA` within the AEA framework.

The `connection.py` module in the `connections` directory contains a `Connection` class, 
which is a wrapper for an SDK or API

An `AEA` can interact with multiple connections at the same time.

## Configuration

The `connection.yaml` file in the agent directory contains protocol details and connection url and port details. For example, the oef `connection.yaml` contains the connection class name, supported protocols, and any connection configuration details.

``` json
name: oef
author: fetchai
version: 0.1.0
license: Apache 2.0
fingerprint: ""
description: "The oef connection provides a wrapper around the OEF sdk."
class_name: OEFConnection
protocols: ["fetchai/oef:0.1.0", "fetchai/fipa:0.1.0"]
restricted_to_protocols: []
excluded_protocols: ["fetchai/gym:0.1.0"]
config:
  addr: ${OEF_ADDR:127.0.0.1}
  port: ${OEF_PORT:10000}
dependencies:
  colorlog: {}
  oef:
    version: ==0.8.1
```


The developer is left to implement the methods of the `Connection` dependent on the protocol type. 

<!--We'll demonstrate implementations from the `oef` connection as an example.-->


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
### `from_config(cls, address: Address, connection_configuration: ConnectionConfig)`
<!--
``` python
@classmethod
   	def from_config(cls, address: Address, connection_configuration: ConnectionConfig) -> 'Connection':
        oef_addr = cast(str, connection_configuration.config.get("addr"))
        oef_port = cast(int, connection_configuration.config.get("port"))
        return OEFConnection(address, oef_addr, oef_port)
```
-->


<br />




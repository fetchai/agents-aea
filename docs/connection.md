A `Connection` is attached to an `AEA` within the AEA framework.

The `connection.py` module in the `connections` directory contains a `Connection` class, 
which is a wrapper for an SDK or API

An `AEA` can interact with multiple connections at the same time.

## Configuration

The `connection.yaml` file in the agent directory contains protocol details and connection url and port details. For example, the oef `connection.yaml` contains the connection class name, supported protocols, and any connection configuration details.

``` json
name: oef
authors: Fetch.ai Limited
version: 0.1.0
license: Apache 2.0
url: ""
class_name: OEFConnection
supported_protocols: ["oef"]
config:
  addr: 127.0.0.1
  port: 10000

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


## Launching `oef` connections

### `oef` - local node

Download the scripts directory:
``` bash
svn export https://github.com/fetchai/agents-aea.git/trunk/scripts
```

Then, start an oef from a separate terminal:

``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

This pulls and runs an `oef` docker image.

Now you can run an AEA with an `oef` connection.


### `oef` - remote node

Connect directly to a running `oef` via a given `URL:PORT`. Update the configuration of the `oef` connection in the `connection.yaml` file.


<br />




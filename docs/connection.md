A `Connection` is attached to an `AEA` within the AEA framework.

The `connection.py` module in the `connections` directory contains a `Connection` class, 
which is a wrapper for an SDK or API

An `AEA` can interact with multiple connections at the same time.

## Configuration

The `connection.yaml` file in the AEA directory contains protocol details and connection url and port details. For example, the oef `connection.yaml` contains the connection class name, supported protocols, and any connection configuration details.

``` yaml
name: oef
author: fetchai
version: 0.1.0
license: Apache-2.0
fingerprint: ""
description: "The oef connection provides a wrapper around the OEF SDK for connection with the OEF search and communication node."
class_name: OEFConnection
protocols: ["fetchai/oef_search:0.1.0", "fetchai/fipa:0.1.0"]
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

<br />




A `Connection` is attached to an `AEA` within the AEA framework.

The `connection.py` module in the `connections` directory contains a `Connection` class, 
which is a wrapper for an SDK or API

An `AEA` can interact with multiple connections at the same time.

## Configuration

The `connection.yaml` file in the AEA directory contains protocol details and connection url and port details. For example, the oef `connection.yaml` contains the connection class name, supported protocols, and any connection configuration details.

The developer is left to implement the methods of the `Connection` dependent on the protocol type. 

<br />




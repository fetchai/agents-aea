# P2P Libp2p Client Connection

A lightweight TCP connection to a libp2p DHT node.

It allows for using the DHT without having to deploy a node by delegating its communication traffic to an already running DHT node with delegate service enabled.


## Usage 

First, add the connection to your AEA project: `aea add connection fetchai/p2p_libp2p_client:0.19.0`.

Next, ensure that the connection is properly configured by setting:

- `nodes` to a list of `uri`s, connection will choose the delegate randomly
- `uri` to the public IP address and port number of the delegate service of a running DHT node, in format `${ip|dns}:${port}`

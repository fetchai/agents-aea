# P2P Libp2p Connection

This connection enables point-to-point secure end-to-end encrypted communication between agents in a fully decentralized way.
The connection deploys a node that collectively maintains a distributed hash table (DHT) along with other nodes in the same network.
The DHT provides proper messages delivery by mapping agents addresses to their locations.

## Usage

First, add the connection to your AEA project: `aea add connection fetchai/p2p_libp2p:0.25.0`.

Next, ensure that the connection is properly configured by setting:

- `local_uri` to the local IP address and port number that the node should use, in format `${ip}:${port}`
- `public_uri` to the external IP address and port number allocated for the node, can be the same as `local_uri` if running locally
- `entry_peers` to a list of multiaddresses of already deployed nodes to join their network, should be empty for genesis node
- `delegate_uri` to the IP address and port number for the delegate service, leave empty to disable the service

If the delegate service is enabled, then other AEAs can connect to the peer node using the `fetchai/p2p_libp2p_client:0.19.0` connection.

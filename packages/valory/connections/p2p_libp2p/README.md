# P2P Libp2p Connection

This connection enables point-to-point secure end-to-end encrypted communication between agents in a fully decentralized way.
The connection deploys a node that collectively maintains a distributed hash table (DHT) along with other nodes in the same network.
The DHT provides proper messages delivery by mapping agents addresses to their locations.

## Usage

First, add the connection to your AEA project: `aea add connection valory/p2p_libp2p:0.26.0`.

Next, ensure that the connection is properly configured by setting:

- `local_uri` to the local IP address and port number that the node should use, in format `${ip}:${port}`
- `public_uri` to the external IP address and port number allocated for the node, can be the same as `local_uri` if running locally
- `entry_peers` to a list of multiaddresses of already deployed nodes to join their network, should be empty for genesis node
- `delegate_uri` to the IP address and port number for the delegate service, leave empty to disable the service

If the delegate service is enabled, then other AEAs can connect to the peer node using the `valory/p2p_libp2p_client:0.20.0` connection.


## Example: setting up the ACN locally

Cosmos uses the secp256k1 key format that we require for the ACN's proof of representation.
We can easily generate keys on demand using the open-aea framework:

```bash
function setup {
    aea create $1 --local
    cd $1
    aea generate-key cosmos && \
    aea add-key cosmos && \
    echo "" && echo "created agent: $1"
    echo "    private key: $(cat cosmos_private_key.txt | tr -d \\n )" && \
    echo "    public key:  $(aea get-public-key cosmos)" && \
    echo "    PeerID:      $(aea get-multiaddress cosmos)" && \
    echo "" && cd ../ && rm -r $1
}

setup bootstrap_peer
setup entry_node_1
setup entry_node_2
```

The output looks as follows:
```bash
Initializing AEA project 'bootstrap_peer'
Creating project directory './bootstrap_peer'
Creating config file aea-config.yaml
Adding default packages ...
Adding protocol 'open_aea/signing:1.0.0:bafybeiambqptflge33eemdhis2whik67hjplfnqwieoa6wblzlaf7vuo44'...
Successfully added protocol 'open_aea/signing:1.0.0'.

created agent: bootstrap_peer
    private key: 401e39213ca22d324c3259b51585571948139cdd0ba0e3d34d93b61bbea292b5
    public key:  025d1076b5571ac239bd269bcd5a6a004d035c17ad8b3de899fa6144e8f57d3310
    PeerID:      16Uiu2HAm1gxTRqk1ao3WYTE7bNR78f3sqriWLtWpfNNVP1T66B2P

...
created agent: entry_node_1
    private key: db26b697be0e6fc02bbe147050e1eeb847bc98b7f2ffbd1f0eb06922786a3eb4
    public key:  035198c3e4517b3be0f3ae61387c2e92427c04bae33486cc9fa6e9b39a52e32c4f
    PeerID:      16Uiu2HAmJ9WUpYQKefzwgxJtceyTjFEidMHP8MHAcbfkrZKwuQSi

...
created agent: entry_node_2
    private key: 1d73b10bc8e4f6e1dd84e644a7d895e6132dfc15fe6e7234bf52f94b90ce9bb6
    public key:  0286bac6348f025fb2ae5a223adc2dc99844546cb4cb6a6dec84bba052ebbaddac
    PeerID:      16Uiu2HAm4Vbo6bv8G2jdYARsm8wNXogFAdL6c87P7uQGTWh7uey9
```

Instructions in the [open-acn README.md](https://github.com/valory-xyz/open-acn)
can than be followed to set up the network.

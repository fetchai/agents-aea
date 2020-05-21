``` bash
aea create my_genesis_aea
cd my_genesis_aea
aea add connection fetchai/p2p_libp2p:0.1.0
aea config set agent.default_connection fetchai/p2p_libp2p:0.1.0
aea run --connections fetchai/p2p_libp2p:0.1.0
```
``` bash
aea create my_other_aea
cd my_other_aea
aea add connection fetchai/p2p_libp2p:0.1.0
aea config set agent.default_connection fetchai/p2p_libp2p:0.1.0
```
``` bash
aea run --connections fetchai/p2p_libp2p:0.1.0
```
``` yaml
config:
  libp2p_entry_peers: [{MULTI_ADDRESSES}]
  libp2p_host: 0.0.0.0
  libp2p_log_file: libp2p_node.log
  libp2p_port: 9001
```

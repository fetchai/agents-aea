``` bash
aea create my_genesis_aea
cd my_genesis_aea
aea add connection fetchai/p2p_noise:0.2.0
aea config set agent.default_connection fetchai/p2p_noise:0.2.0
aea run --connections fetchai/p2p_noise:0.2.0
```
``` bash
aea create my_other_aea
cd my_other_aea
aea add connection fetchai/p2p_noise:0.2.0
aea config set agent.default_connection fetchai/p2p_noise:0.2.0
```
``` bash
aea run --connections fetchai/p2p_noise:0.2.0
```
``` yaml
config:
  noise_entry_peers: ["127.0.0.1:9000"]
  noise_host: 127.0.0.1
  noise_log_file: noise_node.log
  noise_port: 9001
```

``` bash
pip install aea-ledger-fetchai
```
``` bash
aea create my_genesis_aea
cd my_genesis_aea
aea add connection fetchai/p2p_libp2p:0.25.0
aea config set agent.default_connection fetchai/p2p_libp2p:0.25.0
aea install
aea build
```
``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
aea generate-key fetchai fetchai_connection_private_key.txt
aea add-key fetchai fetchai_connection_private_key.txt --connection
aea issue-certificates
```
``` bash
aea run --connections fetchai/p2p_libp2p:0.25.0
```
``` bash
aea create my_other_aea
cd my_other_aea
aea add connection fetchai/p2p_libp2p:0.25.0
aea config set agent.default_connection fetchai/p2p_libp2p:0.25.0
aea install
aea build
```
``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
aea generate-key fetchai fetchai_connection_private_key.txt
aea add-key fetchai fetchai_connection_private_key.txt --connection
aea issue-certificates
```
``` bash
aea config set --type dict vendor.fetchai.connections.p2p_libp2p.config \
'{
  "delegate_uri": "127.0.0.1:11001",
  "entry_peers": ["SOME_ADDRESS"],
  "local_uri": "127.0.0.1:9001",
  "log_file": "libp2p_node.log",
  "public_uri": "127.0.0.1:9001"
}'
```
``` bash
aea run --connections fetchai/p2p_libp2p:0.25.0
```
  ``` bash
  svn export https://github.com/fetchai/agents-aea.git/trunk/packages/fetchai/connections/p2p_libp2p
  cd p2p_libp2p
  go build
  chmod +x libp2p_node
  ```
  ``` bash
  docker build -t acn_node_standalone -f scripts/acn/Dockerfile .
  ```
  ``` bash
  python3 run_acn_node_standalone.py libp2p_node --config-from-env
  ```
  ``` bash
  python3 run_acn_node_standalone.py libp2p_node --config-from-file <env-file-path>
  ```
  ``` bash
  docker run -v <acn_config_file>:/acn/acn_config -it acn_node_standalone --config-from-file /acn/acn_config
  ```
  ``` bash
  python3 run_acn_node_standalone.py libp2p_node --key-file <node_private_key.txt> \
    --uri <AEA_P2P_URI> --uri-external <AEA_P2P_URI_PUBLIC>  \
    --uri-delegate <AEA_P2P_DELEGATE_URI> \
    --entry-peers-maddrs <AEA_P2P_ENTRY_URI_1> <AEA_P2P_ENTRY_URI_2> ...
  ```
  ``` bash
  docker run -v <node_private_key.txt>:/acn/key.txt -it acn_node_standalone --key-file /acn/key.txt \
    --uri <AEA_P2P_URI> --uri-external <AEA_P2P_URI_PUBLIC>  \
    --uri-delegate <AEA_P2P_DELEGATE_URI> \
    --entry-peers-maddrs <AEA_P2P_ENTRY_URI_1> <AEA_P2P_ENTRY_URI_2> ...
  ```
``` yaml
/dns4/acn.fetch.ai/tcp/9000/p2p/16Uiu2HAkw1ypeQYQbRFV5hKUxGRHocwU5ohmVmCnyJNg36tnPFdx
/dns4/acn.fetch.ai/tcp/9001/p2p/16Uiu2HAmVWnopQAqq4pniYLw44VRvYxBUoRHqjz1Hh2SoCyjbyRW
```
``` yaml
---
public_id: fetchai/p2p_libp2p:0.25.0
type: connection
config:
  delegate_uri: null
  entry_peers: [/dns4/acn.fetch.ai/tcp/9000/p2p/16Uiu2HAkw1ypeQYQbRFV5hKUxGRHocwU5ohmVmCnyJNg36tnPFdx,/dns4/acn.fetch.ai/tcp/9001/p2p/16Uiu2HAmVWnopQAqq4pniYLw44VRvYxBUoRHqjz1Hh2SoCyjbyRW]
  public_uri: null
  local_uri: 127.0.0.1:9001
```
``` bash
aea create my_genesis_aea
cd my_genesis_aea
aea add connection fetchai/p2p_libp2p:0.8.0
aea config set agent.default_connection fetchai/p2p_libp2p:0.8.0
aea run --connections fetchai/p2p_libp2p:0.8.0
```
``` bash
aea create my_other_aea
cd my_other_aea
aea add connection fetchai/p2p_libp2p:0.8.0
aea config set agent.default_connection fetchai/p2p_libp2p:0.8.0
```
``` bash
aea run --connections fetchai/p2p_libp2p:0.8.0
```
``` bash
aea fetch fetchai/weather_station:0.11.0
aea fetch fetchai/weather_client:0.11.0
```
``` bash
aea add connection fetchai/p2p_libp2p:0.8.0
aea config set agent.default_connection fetchai/p2p_libp2p:0.8.0
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```
``` bash
aea run --connections "fetchai/p2p_libp2p:0.8.0,fetchai/oef:0.8.0"
```
``` bash
My libp2p addresses: ...
```
``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
```
``` bash
aea generate-wealth fetchai
```
``` bash
svn export https://github.com/fetchai/agents-aea.git/trunk/packages/fetchai/connections/p2p_libp2p
cd p2p_libp2p
```
``` bash
go build
```
``` bash
aea run --connections "fetchai/p2p_libp2p:0.8.0,fetchai/oef:0.8.0"
```
``` bash
chmod +x libp2p_node
```
``` bash
./libp2p_node .env.libp2p
```
``` yaml
config:
  delegate_uri: 127.0.0.1:11001
  entry_peers: MULTI_ADDRESSES
  local_uri: 127.0.0.1:9001
  log_file: libp2p_node.log
  public_uri: 127.0.0.1:9001
```
``` yaml
default_routing:
  ? "fetchai/oef_search:0.5.0"
  : "fetchai/oef:0.8.0"
```
``` yaml
config:
  delegate_uri: 127.0.0.1:11001
  entry_peers: MULTI_ADDRESSES
  local_uri: 127.0.0.1:9001
  log_file: libp2p_node.log
  public_uri: 127.0.0.1:9001
```
```yaml
/dns4/agents-p2p-dht.sandbox.fetch-ai.com/tcp/9000/p2p/16Uiu2HAkw1ypeQYQbRFV5hKUxGRHocwU5ohmVmCnyJNg36tnPFdx
/dns4/agents-p2p-dht.sandbox.fetch-ai.com/tcp/9001/p2p/16Uiu2HAmVWnopQAqq4pniYLw44VRvYxBUoRHqjz1Hh2SoCyjbyRW
```
``` yaml
config:
  delegate_uri: 127.0.0.1:11001
  entry_peers: [/dns4/agents-p2p-dht.sandbox.fetch-ai.com/tcp/9000/p2p/16Uiu2HAkw1ypeQYQbRFV5hKUxGRHocwU5ohmVmCnyJNg36tnPFdx,/dns4/agents-p2p-dht.sandbox.fetch-ai.com/tcp/9001/p2p/16Uiu2HAmVWnopQAqq4pniYLw44VRvYxBUoRHqjz1Hh2SoCyjbyRW]
  local_uri: 127.0.0.1:9001
  log_file: libp2p_node.log
  public_uri: 127.0.0.1:9001
```
``` txt
AEA_AGENT_ADDR=cosmos1azvdhesjk739d2j0xdmhyzlu3kfvqqje9r7uay
AEA_P2P_ID=1ceb61fb96132480c8a8bc3023801e626fff0f871965858584744ed5a6299773
AEA_P2P_URI=127.0.0.1:9001
AEA_P2P_ENTRY_URIS=/dns4/127.0.0.1/tcp/9000/p2p/16Uiu2HAm6ghFe59TZ2vHQCcr1dx5P4WWEEAfVp5K6jcgmXjG8bGQ
NODE_TO_AEA=033a2-libp2p_to_aea
AEA_TO_NODE=033a2-aea_to_libp2p
AEA_P2P_URI_PUBLIC=127.0.0.1:9001
AEA_P2P_DELEGATE_URI=127.0.0.1:11001
```
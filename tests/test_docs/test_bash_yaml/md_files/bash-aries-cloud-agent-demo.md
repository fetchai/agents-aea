``` bash
pip install aries-cloudagent
```
``` bash
./manage build
./manage start --logs
``` 
``` bash
aca-py start --help
```
``` bash
aca-py start --admin 127.0.0.1 8021 --admin-insecure-mode --inbound-transport http 0.0.0.0 8020 --outbound-transport http --webhook-url http://127.0.0.1:8022/webhooks
```
``` bash
aca-py start --admin 127.0.0.1 8031 --admin-insecure-mode --inbound-transport http 0.0.0.0 8030 --outbound-transp http --webhook-url http://127.0.0.1:8032/webhooks
```
``` bash
aea fetch fetchai/aries_alice:0.31.0
cd aries_alice
```
``` bash
aea create aries_alice
cd aries_alice
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/http_client:0.23.0
aea add connection fetchai/webhook:0.19.0
aea add skill fetchai/aries_alice:0.24.0
```
``` bash
aea config set vendor.fetchai.skills.aries_alice.models.strategy.args.admin_host 127.0.0.1
```
``` bash
aea config set --type int vendor.fetchai.skills.aries_alice.models.strategy.args.admin_port 8031
```
``` bash
aea config set --type int vendor.fetchai.connections.webhook.config.webhook_port 8032
```
``` bash
aea config set vendor.fetchai.connections.webhook.config.webhook_url_path /webhooks/topic/{topic}/
```
``` bash
aea config set --type dict vendor.fetchai.connections.p2p_libp2p.config \
'{
  "delegate_uri": "127.0.0.1:11000",
  "entry_peers": [],
  "local_uri": "127.0.0.1:7000",
  "log_file": "libp2p_node.log",
  "public_uri": "127.0.0.1:7000"
}'
```
``` bash
aea install
aea build
```
``` bash
aea run
```
``` bash
aea fetch fetchai/aries_faber:0.31.0
cd aries_faber
```
``` bash
aea create aries_faber
cd aries_faber
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/http_client:0.23.0
aea add connection fetchai/webhook:0.19.0
aea add skill fetchai/aries_faber:0.22.0
```
``` bash
aea config set vendor.fetchai.skills.aries_faber.models.strategy.args.admin_host 127.0.0.1
```
``` bash
aea config set --type int vendor.fetchai.skills.aries_faber.models.strategy.args.admin_port 8021
```
``` bash
aea config set --type int vendor.fetchai.connections.webhook.config.webhook_port 8022
```
``` bash
aea config set vendor.fetchai.connections.webhook.config.webhook_url_path /webhooks/topic/{topic}/
```
``` bash
aea config set --type dict vendor.fetchai.connections.p2p_libp2p.config \
'{
  "delegate_uri": "127.0.0.1:11001",
  "entry_peers": ["SOME_ADDRESS"],
  "local_uri": "127.0.0.1:7001",
  "log_file": "libp2p_node.log",
  "public_uri": "127.0.0.1:7001"
}'
```
``` bash
aea install
aea build
```
``` bash
aea run
```
``` bash
aea delete aries_faber
aea delete aries_alice
```
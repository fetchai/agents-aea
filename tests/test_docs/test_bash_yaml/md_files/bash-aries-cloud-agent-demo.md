``` bash
pip install aries-cloudagent
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
aea create aries_alice
cd aries_alice
```
``` bash
aea add skill fetchai/aries_alice:0.1.0
```
``` bash
aea config set vendor.fetchai.skills.aries_alice.handlers.aries_demo_default.args.admin_host 127.0.0.1
```
``` bash
aea config set vendor.fetchai.skills.aries_alice.handlers.aries_demo_http.args.admin_host 127.0.0.1
```
``` bash
aea config set --type int vendor.fetchai.skills.aries_alice.handlers.aries_demo_default.args.admin_port 8031
```
``` bash
aea config set --type int vendor.fetchai.skills.aries_alice.handlers.aries_demo_http.args.admin_port 8031
```
``` bash
aea add connection fetchai/http_client:0.2.0
aea add connection fetchai/webhook:0.1.0
aea add connection fetchai/oef:0.3.0
```
``` bash
aea config set --type int vendor.fetchai.connections.webhook.config.webhook_port 8032
```
``` bash
aea config set vendor.fetchai.connections.webhook.config.webhook_url_path /webhooks/topic/{topic}/
```
``` bash
aea config set agent.default_connection fetchai/oef:0.3.0
```
``` bash
aea fetch fetchai/aries_alice:0.1.0 
cd aries_alice
```
``` bash
aea config set vendor.fetchai.skills.aries_alice.handlers.aries_demo_default.args.admin_host 127.0.0.1
```
``` bash
aea config set vendor.fetchai.skills.aries_alice.handlers.aries_demo_http.args.admin_host 127.0.0.1
```
``` bash
aea config set --type int vendor.fetchai.skills.aries_alice.handlers.aries_demo_default.args.admin_port 8031
```
``` bash
aea config set --type int vendor.fetchai.skills.aries_alice.handlers.aries_demo_http.args.admin_port 8031
```
``` bash
aea config set --type int vendor.fetchai.connections.webhook.config.webhook_port 8032
```
``` bash
aea config set vendor.fetchai.connections.webhook.config.webhook_url_path /webhooks/topic/{topic}/
```
``` bash
aea install
```
``` bash
aea run
```
``` bash
My address is: YrP7H2qdCb3VyPwpQa53o39cWCDHhVcjwCtJLes6HKWM8FpVK
```
``` bash
aea create aries_faber
cd aries_faber
```
``` bash
aea add skill fetchai/aries_faber:0.1.0
```
``` bash
aea config set vendor.fetchai.skills.aries_faber.behaviours.aries_demo_faber.args.admin_host 127.0.0.1
```
``` bash
aea config set vendor.fetchai.skills.aries_faber.handlers.aries_demo_http.args.admin_host 127.0.0.1
```
``` bash
aea config set --type int vendor.fetchai.skills.aries_faber.behaviours.aries_demo_faber.args.admin_port 8021
```
``` bash
aea config set --type int vendor.fetchai.skills.aries_faber.handlers.aries_demo_http.args.admin_port 8021
```
``` bash
aea config set vendor.fetchai.skills.aries_faber.handlers.aries_demo_http.args.alice_id <Alice_AEA's address>
```
``` bash
aea add connection fetchai/http_client:0.2.0
aea add connection fetchai/webhook:0.1.0
aea add connection fetchai/oef:0.3.0
```
``` bash
aea config set --type int vendor.fetchai.connections.webhook.config.webhook_port 8022
```
``` bash
aea config set vendor.fetchai.connections.webhook.config.webhook_url_path /webhooks/topic/{topic}/
```
``` bash
aea config set agent.default_connection fetchai/http_client:0.2.0
```
``` bash
aea fetch fetchai/aries_faber:0.1.0 
cd aries_faber
```
``` bash
aea config set vendor.fetchai.skills.aries_faber.behaviours.aries_demo_faber.args.admin_host 127.0.0.1
```
``` bash
aea config set vendor.fetchai.skills.aries_faber.handlers.aries_demo_http.args.admin_host 127.0.0.1
```
``` bash
aea config set --type int vendor.fetchai.skills.aries_faber.behaviours.aries_demo_faber.args.admin_port 8021
```
``` bash
aea config set --type int vendor.fetchai.skills.aries_faber.handlers.aries_demo_http.args.admin_port 8021
```
``` bash
aea config set vendor.fetchai.skills.aries_faber.handlers.aries_demo_http.args.alice_id <Alice_AEA's address>
```
``` bash
aea config set --type int vendor.fetchai.connections.webhook.config.webhook_port 8022
```
``` bash
aea config set vendor.fetchai.connections.webhook.config.webhook_url_path /webhooks/topic/{topic}/
```
``` bash
aea install
```
``` bash
aea run
```
``` bash
aea delete aries_faber
aea delete aries_alice
```   

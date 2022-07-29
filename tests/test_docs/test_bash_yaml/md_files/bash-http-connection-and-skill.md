``` bash
aea create my_aea
cd my_aea
```
``` bash
aea add connection fetchai/http_server:0.22.0:bafybeifpu6bxwhmc7rtcyi4u6pgkzmn57qielr5d4ygvyhuyb44pfkqf3i --remote
```
``` bash
aea config set agent.default_connection fetchai/http_server:0.22.0
```
``` bash
aea config set vendor.fetchai.connections.http_server.config.api_spec_path "../examples/http_ex/petstore.yaml"
```
``` bash
aea generate-key ethereum
aea add-key ethereum
```
``` bash
aea install
```
``` bash
aea scaffold skill http_echo
```
``` bash
aea fingerprint skill fetchai/http_echo:0.20.0
```
``` bash
aea config set vendor.fetchai.connections.http_server.config.target_skill_id "$(aea config get agent.author)/http_echo:0.1.0"
```
``` bash
aea run
```
``` yaml
handlers:
  http_handler:
    args: {}
    class_name: HttpHandler
models:
  default_dialogues:
    args: {}
    class_name: DefaultDialogues
  http_dialogues:
    args: {}
    class_name: HttpDialogues
```

``` bash
mkdir packages
aea create my_aea
cd my_aea
aea add connection fetchai/http_server:0.22.0:bafybeifpu6bxwhmc7rtcyi4u6pgkzmn57qielr5d4ygvyhuyb44pfkqf3i --remote
aea push connection fetchai/http_server --local
aea add protocol fetchai/default:1.0.0:bafybeicqyilg4a45ezogmfancp7dc2j7lyaevw6vqcsxs76f7f53qpp4ii --remote
aea push protocol fetchai/default --local
aea add protocol fetchai/http:1.0.0:bafybeif6axlnlm37vqtlthra2evrbhaenxn7qyayi4ajgnany6ajsr256q --remote
aea push protocol fetchai/http --local
cd ..
aea delete my_aea
```
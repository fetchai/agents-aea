``` bash
aea create my_aea
cd my_aea
```
``` bash
aea add connection fetchai/http_server:0.22.0:bafybeihvncr2inhj2i6lki6qsa2z64bmxa6hononcf5nuvojsygsgqycma --remote
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
aea add connection fetchai/http_server:0.22.0:bafybeihvncr2inhj2i6lki6qsa2z64bmxa6hononcf5nuvojsygsgqycma --remote
aea push connection fetchai/http_server --local
aea add protocol fetchai/default:1.0.0:bafybeic72ebyh7j4sqfa4fltvf7hm5taq2gtb43rnko3recmbr4b4vzcny --remote
aea push protocol fetchai/default --local
aea add protocol fetchai/http:1.0.0:bafybeihpthltayuvcx2ja3wy45qiao4z3bgszgz4gvebycbfx7qokznqpu --remote
aea push protocol fetchai/http --local
cd ..
aea delete my_aea
```
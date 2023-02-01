``` bash
aea create my_aea
cd my_aea
```
``` bash
aea add connection fetchai/http_server:0.22.0:bafybeihaax5od5zo5jk2l62hv4jwuwtxloh5mijozudpsjombqc4ncmi6i --remote
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
aea add connection fetchai/http_server:0.22.0:bafybeihaax5od5zo5jk2l62hv4jwuwtxloh5mijozudpsjombqc4ncmi6i --remote
aea push connection fetchai/http_server --local
aea add protocol fetchai/default:1.0.0:bafybeieqqzgzuappi2ped42upgzad5gt3mxiyjhojwibxm4o367ffsian4 --remote
aea push protocol fetchai/default --local
aea add protocol valory/http:1.0.0:bafybeifyoio7nlh5zzyn5yz7krkou56l22to3cwg7gw5v5o3vxwklibhty --remote
aea push protocol valory/http --local
cd ..
aea delete my_aea
```
``` bash
aea create my_aea
cd my_aea
```
``` bash
aea add connection fetchai/http_server:0.22.0:bafybeiaf2w3jfemqu4zrtfzewexh5ttqytvhv4tqfzcrv6qxsqnxrv7eu4 --remote
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
aea add connection fetchai/http_server:0.22.0:bafybeiaf2w3jfemqu4zrtfzewexh5ttqytvhv4tqfzcrv6qxsqnxrv7eu4 --remote
aea push connection fetchai/http_server --local
aea add protocol fetchai/default:1.0.0:bafybeihzesahyayexkhk26fg7rqnjuqaab3bmcijtjekvskvs4xw6ecyuu --remote
aea push protocol fetchai/default --local
aea add protocol valory/http:1.0.0:bafybeigzqo2zaakcjtzzsm6dh4x73v72xg6ctk6muyp5uq5ueb7y34fbxy --remote
aea push protocol valory/http --local
cd ..
aea delete my_aea
```
``` bash
aea create my_aea
cd my_aea
```
``` bash
aea add connection fetchai/http_server:0.22.0:QmbJ2Bcv156rY4ikSc7RB6Z4EwsXeZW1MqvdYcjw4kKY9z --remote
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
aea add connection fetchai/http_server:0.22.0:QmbJ2Bcv156rY4ikSc7RB6Z4EwsXeZW1MqvdYcjw4kKY9z --remote
aea push connection fetchai/http_server --local
aea add protocol fetchai/default:1.0.0:QmWoiXYAKqwyqXDQ4gC1b11uRAxKRBiicWWuqthqeNWyEw --remote
aea push protocol fetchai/default --local
aea add protocol fetchai/http:1.0.0:Qmdz2FD7P9VXzUMZpLUh3DV5YtgWZwJKDxxw78heeaHv4M --remote
aea push protocol fetchai/http --local
cd ..
aea delete my_aea
```
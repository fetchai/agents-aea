``` bash
aea create my_aea
cd my_aea
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
aea add connection fetchai/http_server:0.22.0:QmbTKQYumbrBQBwSy91GyEhKr4kgGD2S9rHjybb3EDD8PA --remote
aea add protocols fetchai/default:1.0.0:QmYNdsSrdKRvJGKjAbREuvkjGXgnanDjxCBS8CfJb9fzr1 --remote
aea add protocols fetchai/http:1.0.0:QmVUoaxD2pMd2czgrUjFH6LifM8h9KUt4TzRRPjUHCCYyv --remote
```
``` bash
aea create my_aea
cd my_aea
```
``` bash
aea add connection fetchai/http_server:0.21.0
```
``` bash
aea config set agent.default_connection fetchai/http_server:0.21.0
```
``` bash
aea config set vendor.fetchai.connections.http_server.config.api_spec_path "../examples/http_ex/petstore.yaml"
```
``` bash
aea generate-key fetchai
aea add-key fetchai
```
``` bash
aea install
```
``` bash
aea scaffold skill http_echo
```
``` bash
aea fingerprint skill fetchai/http_echo:0.19.0
```
``` bash
aea run
```
``` yaml
handlers:
  http_handler:
    args: {}
    class_name: HttpHandler
```
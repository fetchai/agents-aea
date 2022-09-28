``` yaml
agent_name: http_echo
author: open_aea
version: 0.1.0
license: Apache-2.0
description: Http echo agent configured with default variables.
aea_version: '>=1.3.0, <2.0.0'
fingerprint: {}
fingerprint_ignore_patterns: []
connections:
- fetchai/http_server:0.22.0
contracts: []
protocols:
- fetchai/default:1.0.0
- valory/http:1.0.0
- open_aea/signing:1.0.0
skills:
- fetchai/http_echo:0.20.0
default_ledger: ethereum
required_ledgers:
- ethereum
default_routing: {}
connection_private_key_paths: {}
private_key_paths:
  ethereum: ethereum_private_key.txt
logging_config:
  disable_existing_loggers: false
  version: 1
dependencies:
  open-aea-ledger-ethereum: {}
default_connection: null
---
public_id: fetchai/http_server:0.22.0
type: connection
config:
  host: ${HOST:str:localhost}
  port: ${PORT:int:5000}
  target_skill_id: ${TARGET_SKILL:str:fetchai/http_echo:0.20.0}
```

``` yaml
host: ${HOST:str:localhost}
port: ${PORT:int:5000}
target_skill_id: ${TARGET_SKILL:str:fetchai/http_echo:0.20.0}
```

``` yaml
${ENVIRONMENT_VALUE:PYTHON_TYPE:DEFAULT_VALUE}
```

``` bash
aea run --aev
```

``` bash
    _     _____     _
   / \   | ____|   / \
  / _ \  |  _|    / _ \
 / ___ \ | |___  / ___ \
/_/   \_\|_____|/_/   \_\

v1.4.0

Starting AEA 'http_echo' in 'async' mode...
info: [http_echo] HTTP Server has connected to port: 5000.
info: [http_echo] Start processing messages...
```

``` bash
curl localhost:5000
{"tom": {"type": "cat", "age": 10}}
```

``` bash
export PORT=8081
aea run --aev
    _     _____     _
   / \   | ____|   / \
  / _ \  |  _|    / _ \
 / ___ \ | |___  / ___ \
/_/   \_\|_____|/_/   \_\

v1.4.0

Starting AEA 'http_echo' in 'async' mode...
info: [http_echo] HTTP Server has connected to port: 8081.
info: [http_echo] Start processing messages...
```

``` bash
curl localhost:8081
{"tom": {"type": "cat", "age": 10}}
```

``` bash
aea delete http_echo
```

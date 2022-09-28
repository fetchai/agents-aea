# Configuring with Environment Variables

The purpose of this demonstration is to show the `open-aea` framework can dynamically configure agents from environment variables.

A full break down of the development flow is covered within the <a href="../quickstart/">Development Quickstart</a>.

It is highly recommended that developers begin by following the quick start!

After you have followed the quick start, create a <a href="../http-echo-demo/">HTTP Echo Agent</a>. 

It is assumed that developers are within a pipenv virtual environment.

Notice, that the configuration of the AEA is as so;


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

Notice how the ```fetchai/http_server:0.22.0``` has a number of override parameters specified:
``` yaml
host: ${HOST:str:localhost}
port: ${PORT:int:5000}
target_skill_id: ${TARGET_SKILL:str:fetchai/http_echo:0.20.0}
``` 

Please notice the values provided to the over-rides. The syntax is as follows;

``` yaml
${ENVIRONMENT_VALUE:PYTHON_TYPE:DEFAULT_VALUE}
```


We can use environment variables to override these default values.

First run the agent with the default port (assuming you are within the agent directory created within <a href="../http-echo-demo/">HTTP Echo Agent</a>) as so:

``` bash
aea run --aev
```

The ```--aev``` flag specifies to apply environment overrides

The AEA will then start a web server as so:


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


We can interact with this server using curl in another terminal as so;

``` bash
curl localhost:5000
{"tom": {"type": "cat", "age": 10}}
```


In order to use the environment overrides, we must first stop our AEA. Once the AEA is stopped:

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

We can confirm that we are now serving on a different port as so;

``` bash
curl localhost:8081
{"tom": {"type": "cat", "age": 10}}
```


Congratulations! You have just used an AEA successfully as a web server!

# Tear Down
``` bash
aea delete http_echo
```


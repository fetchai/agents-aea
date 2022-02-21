# Configuring with Environment Variables
The purpose of this demonstration is to show the Open-AEA framework can dynamically configure agents from environment variables.

A full break down of the development flow is covered within the <a href="../quickstart/">Development Quickstart</a>.

It is highly recommended that developers begin by following the quick start!

After you have followed the quick start, create a <a href="../http_echo_demo/">HTTP Echo Agent</a>. 


Notice, that the configuration of the aea is looks like so;

    (open-aea) ~/D/c/v/o/http_echo> cat aea-config.yaml
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
    - fetchai/http:1.0.0
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

Notice how the ```fetchai/http_server:0.22.0``` has a number of override parameters specified:

      host: ${HOST:str:localhost}
      port: ${PORT:int:5000}
      target_skill_id: ${TARGET_SKILL:str:fetchai/http_echo:0.20.0}


Please notice the values provided to the over-rides. The syntax is as follows;

    ${ENVIRONMENT_VALUE:PYTHON_TYPE:DEFAULT_VALUE}


We can use environment variables to override these default values like so

First run the agent with the default port (assuming you are within the agent directory created within <a href="../http_echo_demo/">HTTP Echo Agent</a>) as so:

    aea run --aev

The ```--aev``` flag specifies to apply environment overrides

The aea will ten start a webserver as so:

        _     _____     _    
       / \   | ____|   / \   
      / _ \  |  _|    / _ \  
     / ___ \ | |___  / ___ \ 
    /_/   \_\|_____|/_/   \_\
                             
    v1.4.0
    
    Starting AEA 'http_echo' in 'async' mode...
    info: [http_echo] HTTP Server has connected to port: 5000.
    info: [http_echo] Start processing messages...


We can interact with this server using curl in another terminal as so;

    curl localhost:5000
    {"tom": {"type": "cat", "age": 10}}


In order to use the environment overrides, we must first stop our AEA. Once the AEA is stopped:
    
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

We can confirm that we are now serving on a different port as so;

    curl localhost:8081
    {"tom": {"type": "cat", "age": 10}}

A full break down of the development flow is covered within the <a href="../quickstart/">Development Quickstart</a>. 
The easiest way to get started with the http server is to use our pre-built example skill.



```bash
pipenv shell
aea fetch open_aea/http_echo:0.1.0 --local 
cd http_echo
aea generate-key ethereum; aea add-key ethereum
aea run --aev
Adding protocol 'open_aea/signing:1.0.0'...
Successfully added protocol 'open_aea/signing:1.0.0'.
Adding protocol 'fetchai/http:1.0.0'...
Successfully added protocol 'fetchai/http:1.0.0'.
Adding protocol 'fetchai/default:1.0.0'...
Successfully added protocol 'fetchai/default:1.0.0'.
Adding connection 'fetchai/http_server:0.22.0'...
Successfully added connection 'fetchai/http_server:0.22.0'.
Adding skill 'fetchai/http_echo:0.20.0'...
Successfully added skill 'fetchai/http_echo:0.20.0'.
Agent http_echo successfully fetched.
    _     _____     _    
   / \   | ____|   / \   
  / _ \  |  _|    / _ \  
 / ___ \ | |___  / ___ \ 
/_/   \_\|_____|/_/   \_\
                         
v1.3.0

Starting AEA 'http_echo' in 'async' mode...
info: [http_echo] HTTP Server has connected to port: 5000.
info: [http_echo] Start processing messages...
```

in a second terminal

```bash
curl 0.0.0.0:5000
{"tom": {"type": "cat", "age": 10}}
```
Congratulations! You have just used an AEA successfully as a web server!

# Tear Down
```
aea delete http_echo
```


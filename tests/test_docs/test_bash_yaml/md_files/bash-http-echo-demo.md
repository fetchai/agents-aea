``` bash
pipenv shell
aea fetch open_aea/http_echo:0.1.0:bafybeihxe5mk2gs6k3xxf5rgaqqa5ij2ff74gebcwxskc2dpxvt5rcnyxi --remote
cd http_echo
aea generate-key ethereum; aea add-key ethereum
aea install
aea run --aev
Adding protocol 'open_aea/signing:1.0.0'...
Successfully added protocol 'open_aea/signing:1.0.0'.
Adding protocol 'valory/http:1.0.0'...
Successfully added protocol 'valory/http:1.0.0'.
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

v1.4.0

Starting AEA 'http_echo' in 'async' mode...
info: [http_echo] HTTP Server has connected to port: 5000.
info: [http_echo] Start processing messages...
```

``` bash
curl 0.0.0.0:5000
{"tom": {"type": "cat", "age": 10}}
```

``` bash
aea delete http_echo
```

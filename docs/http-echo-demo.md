# HTTP Echo Demo

The purpose of this demonstration is to show the `open-aea` framework can be used as a HTTP server. More concretely, an AEA with a http server connection and an appropriate skill can be used as a server.


A full break down of the development flow is covered within the <a href="../quickstart/">Development Quickstart</a>.

It is highly recommended that developers begin by following the quick start!

It is assumed that developers are within a pipenv virtual environment.

A full break down of the development flow is covered within the <a href="../quickstart/">Development Quickstart</a>.
The easiest way to get started with the http server is to use our pre-built example skill.



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

in a second terminal

``` bash
curl 0.0.0.0:5000
{"tom": {"type": "cat", "age": 10}}
```

Congratulations! You have just used an AEA successfully as a web server!

# Tear Down
``` bash
aea delete http_echo
```


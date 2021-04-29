# End2end example Go <> Python

## Run example

ensure all dependencies are installed: python, aea, golang

run to launch buyer agent
`./run_buyer.sh`

run in another terminal to launch seller agent 
`./run_seller.sh`

after a while both agents get connected to p2p fetchai network,
perform fipa message exchange and show `FIPA INTERACTION COMPLETE` in output logs

terminate every agent with `ctrl+c`

## Generate protocol

``` bash
aea create temp_agent
cd temp_agent
aea generate protocol -l PATH_TO_SPEC
```
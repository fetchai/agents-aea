# End-to-end example Go <> Python

## Run example

Ensure all dependencies are installed: python, aea and Golang.

To launch the buyer agent run:
`./run_buyer.sh`

In another terminal, to launch the seller agent run:
`./run_seller.sh`

After a while both agents get connected to the ACN, perform a `fetchai/fipa` message exchange and show `FIPA INTERACTION COMPLETE` in output logs.

Terminate every agent with `ctrl+c`.

## Generate protocol

To generate a protocol, use the following approach:

``` bash
aea create temp_agent
cd temp_agent
aea generate protocol -l PATH_TO_SPEC
```

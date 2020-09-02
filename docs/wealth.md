
To fund an AEA for testing on a test-net you need to request some test tokens from a faucet.

Add a private key to the agent:
``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
```
or
``` bash
aea generate-key ethereum
aea add-key ethereum ethereum_private_key.txt
```

## Using a faucet website

First, print the address:
``` bash
aea get-address fetchai
```
or 
``` bash
aea get-address ethereum
```

This will print the address to the console. Copy the address into the clipboard and request test tokens from the faucet <a href="https://explore-testnet.fetch.ai/tokentap" target="_blank">here for Fetch.ai</a> or <a href="https://faucet.metamask.io/" target="_blank">here for Ethereum</a>. It will take a while for the tokens to become available.

Second, after some time, check the wealth associated with the address:
``` bash
aea get-wealth fetchai
```
or
``` bash
aea get-wealth ethereum
```

## Using the cli
Simply generate wealth via the cli:
``` bash
aea generate-wealth fetchai
```
or 
``` bash
aea generate-wealth ethereum
```

<br />

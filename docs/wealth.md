# Generating Wealth

To fund an AEA for testing on a test-net you need to request some test tokens from a faucet.

First, make sure you have installed the crypto plugin
of the target test-net. E.g. for Fetch.AI:

``` bash
pip install aea-ledger-fetchai
```

And for Ethereum:

``` bash
pip install aea-ledger-ethereum
```

Add a private key to the agent

``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
```

or

``` bash
aea generate-key ethereum
aea add-key ethereum ethereum_private_key.txt
```

!!! note
    If you already have keys in your project, the commands prompt you to confirm whether to replace the existing keys.

## Using a Faucet Website

First, print the address:

``` bash
aea get-address fetchai
```

or

``` bash
aea get-address ethereum
```

This will print the address to the console. Copy the address into the clipboard and request test tokens from the faucet <a href="https://explore-dorado.fetch.ai" target="_blank">here for Fetch.ai</a> or <a href="https://faucet.metamask.io/" target="_blank">here for Ethereum</a>. It will take a while for the tokens to become available.

Second, after some time, check the wealth associated with the address:

``` bash
aea get-wealth fetchai
```

or

``` bash
aea get-wealth ethereum
```

## Using the CLI

Simply generate wealth via the CLI:

``` bash
aea generate-wealth fetchai
```

or

``` bash
aea generate-wealth ethereum
```

!!! note
    This approach can be unreliable for non-fetchai test nets.

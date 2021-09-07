
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

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>If you already have keys in your project, the commands will prompt you for confirmation whether or not to replace the existing keys.
</p>
</div>

## Using a faucet website

First, print the address:
``` bash
aea get-address fetchai
```
or 
``` bash
aea get-address ethereum
```

This will print the address to the console. Copy the address into the clipboard and request test tokens from the faucet <a href="https://explore-stargateworld.fetch.ai" target="_blank">here for Fetch.ai</a> or <a href="https://faucet.metamask.io/" target="_blank">here for Ethereum</a>. It will take a while for the tokens to become available.

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

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>This approach can be unreliable for non-fetchai test nets.
</p>
</div>

<br />

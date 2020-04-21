``` bash
aea generate-key fetchai
aea add-key fetchai fet_private_key.txt
```
``` bash
aea generate-key ethereum
aea add-key ethereum eth_private_key.txt
```
``` bash
aea get-address fetchai
``` 
``` bash
aea get-address ethereum
```
``` bash
aea get-wealth fetchai
```
``` bash
aea get-wealth ethereum
```
``` bash
aea generate-wealth fetchai
```
``` bash
aea generate-wealth ethereum
```
``` yaml
ledger_apis:
  fetchai:
    network: testnet
```
``` yaml
ledger_apis:
  fetchai:
    host: testnet.fetch-ai.com
    port: 80
```
``` yaml
ledger_apis:
  ethereum:
    address: https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe
    chain_id: 3
```
``` yaml
ledger_apis:
  ethereum:
    address: https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe
    chain_id: 3
  fetchai:
    network: testnet
```

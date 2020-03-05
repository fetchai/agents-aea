``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```
``` bash
aea create my_erc1155_deploy
cd my_erc1155_deploy
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/erc1155_deploy:0.1.0
aea add contract fetchai/erc1155:0.1.0
aea install
```
``` bash
aea generate-key ethereum
aea add-key ethereum eth_private_key.txt
```
``` bash
aea create my_erc1155_client
cd my_erc1155_client
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/erc1155_client:0.1.0
aea add contract fetchai/erc1155:0.1.0
aea install
```
``` bash
aea generate-key ethereum
aea add-key ethereum eth_private_key.txt
```
``` bash
aea generate-wealth ethereum
```
``` bash
addr: ${OEF_ADDR: 127.0.0.1}
```
``` bash
aea run --connections fetchai/oef:0.1.0
```
``` bash
cd ..
aea delete my_seller_aea
aea delete my_buyer_aea
```
``` yaml
ledger_apis:
  ethereum:
    address: https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe
    chain_id: 3
    gas_price: 50
```
``` yaml
name: erc1155_deploy
author: fetchai
version: 0.1.0
license: Apache-2.0
fingerprint: {}
description: "The erc1155 deploy skill implements the functionality to depoly and interact with a smart contract."
contracts: ['fetchai/erc1155:0.1.0']
behaviours:
  service_registration:
    class_name: ServiceRegistrationBehaviour
    args:
      services_interval: 60
handlers:
  default:
    class_name: FIPAHandler
    args: {}
  transaction:
    class_name: TransactionHandler
    args: {}
models:
  strategy:
    class_name: Strategy
    args:
      ledger_id: 'ethereum'
      is_ledger_tx: True
      nft: 1
      ft: 2
      item_ids: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
      mint_stock: [100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
      from_supply: 10
      to_supply: 0
      value: 0
      search_schema:
        attribute_one:
          name: country
          type: str
          is_required: True
        attribute_two:
          name: city
          type: str
          is_required: True
      search_data:
        country: UK
        city: Cambridge
protocols: ['fetchai/fipa:0.1.0', 'fetchai/oef:0.1.0', 'fetchai/default:0.1.0']
ledgers: ['fetchai']
dependencies:
  vyper: { version: "==0.1.0b12"}
```

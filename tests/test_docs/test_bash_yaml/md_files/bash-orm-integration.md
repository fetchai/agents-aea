``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```
``` bash
aea create my_seller_aea
cd my_seller_aea
aea add connection fetchai/oef:0.2.0
aea add skill fetchai/generic_seller:0.4.0
```
``` bash
aea create my_buyer_aea
cd my_buyer_aea
aea add connection fetchai/oef:0.2.0
aea add skill fetchai/generic_buyer:0.3.0
```
``` bash
aea generate-key fetchai
aea add-key fetchai fet_private_key.txt
```
``` bash
aea generate-key ethereum
aea add-key ethereum eth_private_key.txt
```
``` bash
aea install
```
``` bash
aea generate-wealth fetchai
```
``` bash
aea generate-wealth ethereum
```
``` bash
addr: ${OEF_ADDR: 127.0.0.1}
```
``` bash
aea install
aea config set agent.default_connection fetchai/oef:0.2.0
aea run --connections fetchai/oef:0.2.0
```
``` bash
cd ..
aea delete my_seller_aea
aea delete my_buyer_aea
```
``` yaml
ledger_apis:
  fetchai:
    network: testnet
```
``` yaml
ledger_apis:
  ethereum:
    address: https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe
    chain_id: 3
    gas_price: 50
```
``` yaml
|----------------------------------------------------------------------|
|         FETCHAI                   |           ETHEREUM               |
|-----------------------------------|----------------------------------|
|models:                            |models:                           |
|  dialogues:                       |  dialogues:                      |
|    args: {}                       |    args: {}                      |
|    class_name: Dialogues          |    class_name: Dialogues         |
|  strategy:                        |  strategy:                       |
|    class_name: Strategy           |    class_name: Strategy          |
|    args:                          |    args:                         |
|      total_price: 10              |      total_price: 10             |
|      seller_tx_fee: 0             |      seller_tx_fee: 0            |
|      currency_id: 'FET'           |      currency_id: 'ETH'          |
|      ledger_id: 'fetchai'         |      ledger_id: 'ethereum'       |
|      is_ledger_tx: True           |      is_ledger_tx: True          |
|      has_data_source: True        |      has_data_source: True       |
|      data_for_sale: {}            |      data_for_sale: {}           |
|      search_schema:               |      search_schema:              |
|        attribute_one:             |        attribute_one:            |
|          name: country            |          name: country           |
|          type: str                |          type: str               |
|          is_required: True        |          is_required: True       |
|        attribute_two:             |        attribute_two:            |
|          name: city               |          name: city              |
|          type: str                |          type: str               |
|          is_required: True        |          is_required: True       |
|      search_data:                 |      search_data:                |
|        country: UK                |        country: UK               |
|        city: Cambridge            |        city: Cambridge           |
|dependencies:                      |dependencies:                     |
|  SQLAlchemy: {}                   |  SQLAlchemy: {}                  |    
|----------------------------------------------------------------------|
```
``` yaml
|----------------------------------------------------------------------|
|         FETCHAI                   |           ETHEREUM               |
|-----------------------------------|----------------------------------|
|models:                            |models:                           |  
|  dialogues:                       |  dialogues:                      |
|    args: {}                       |    args: {}                      |
|    class_name: Dialogues          |    class_name: Dialogues         |
|  strategy:                        |  strategy:                       |
|    class_name: Strategy           |    class_name: Strategy          |
|    args:                          |    args:                         |
|      max_price: 40                |      max_price: 40               |
|      max_buyer_tx_fee: 100        |      max_buyer_tx_fee: 200000    |
|      currency_id: 'FET'           |      currency_id: 'ETH'          |
|      ledger_id: 'fetchai'         |      ledger_id: 'ethereum'       |
|      is_ledger_tx: True           |      is_ledger_tx: True          |
|      search_query:                |      search_query:               |
|        search_term: country       |        search_term: country      |
|        search_value: UK           |        search_value: UK          |
|        constraint_type: '=='      |        constraint_type: '=='     |
|ledgers: ['fetchai']               |ledgers: ['ethereum']             |
|----------------------------------------------------------------------| 
```

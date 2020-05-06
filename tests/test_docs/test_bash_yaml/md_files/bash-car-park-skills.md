``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```
``` bash
aea create car_detector
cd car_detector
aea add connection fetchai/oef:0.2.0
aea add skill fetchai/carpark_detection:0.2.0
aea install
aea config set agent.default_connection fetchai/oef:0.2.0
```
``` bash
aea fetch fetchai/car_detector:0.3.0
cd car_detector
aea install
```
``` bash
aea create car_data_buyer
cd car_data_buyer
aea add connection fetchai/oef:0.2.0
aea add skill fetchai/carpark_client:0.2.0
aea install
aea config set agent.default_connection fetchai/oef:0.2.0
```
``` bash
aea fetch fetchai/car_data_buyer:0.3.0
cd car_data_buyer
aea install
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
aea generate-wealth fetchai
```
``` bash
aea generate-wealth ethereum
```
``` bash
aea config set vendor.fetchai.skills.carpark_detection.models.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.carpark_detection.models.strategy.args.ledger_id ethereum
aea config set vendor.fetchai.skills.carpark_detection.models.strategy.args.db_is_rel_to_cwd False --type bool
```
``` bash
aea config set vendor.fetchai.skills.carpark_client.models.strategy.args.max_buyer_tx_fee 6000 --type int
aea config set vendor.fetchai.skills.carpark_client.models.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.carpark_client.models.strategy.args.ledger_id ethereum
```
``` bash
aea run --connections fetchai/oef:0.2.0
```
``` bash
cd ..
aea delete car_detector
aea delete car_data_buyer
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
|  strategy:                        |  strategy:                       |
|     class_name: Strategy          |     class_name: Strategy         |
|    args:                          |    args:                         |
|      data_price_fet: 2000         |      data_price_fet: 2000        |
|      db_is_rel_to_cwd: False      |      db_is_rel_to_cwd: False     |
|      db_rel_dir: ../temp_files    |      db_rel_dir: ../temp_files   |
|      currency_id: 'FET'           |      currency_id: 'ETH'          |
|      ledger_id: 'fetchai'         |      ledger_id: 'ethereum'       |
|      is_ledger_tx: True           |      is_ledger_tx: True          |
|      seller_tx_fee: 0             |      seller_tx_fee: 0            |
|----------------------------------------------------------------------| 
```
``` yaml
|----------------------------------------------------------------------|
|         FETCHAI                   |           ETHEREUM               |
|-----------------------------------|----------------------------------|
|models:                            |models:                           |              
|  strategy:                        |  strategy:                       |
|     class_name: Strategy          |     class_name: Strategy         |
|    args:                          |    args:                         |
|      country: UK                  |      country: UK                 |
|      search_interval: 120         |      search_interval: 120        |
|      no_find_search_interval: 5   |      no_find_search_interval: 5  |
|      max_price: 40000             |      max_price: 40000            |
|      max_detection_age: 36000000  |      max_detection_age: 36000000 |
|      currency_id: 'FET'           |      currency_id: 'ETH'          |
|      ledger_id: 'fetchai'         |      ledger_id: 'ethereum'       |
|      is_ledger_tx: True           |      is_ledger_tx: True          |
|      max_buyer_tx_fee: 6000       |      max_buyer_tx_fee: 6000      |
|ledgers: ['fetchai']               |ledgers: ['ethereum']             |
|----------------------------------------------------------------------| 
```

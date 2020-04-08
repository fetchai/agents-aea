``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```
``` bash
aea create ml_data_provider
cd ml_data_provider
aea add connection fetchai/oef:0.2.0
aea add skill fetchai/ml_data_provider:0.1.0
aea install
aea config set agent.default_connection fetchai/oef:0.2.0
```
``` bash
aea fetch fetchai/ml_data_provider:0.2.0
cd ml_data_provider
```
``` bash
aea install
```
``` bash
aea run --connections fetchai/oef:0.2.0
```
``` bash
aea create ml_model_trainer
cd ml_model_trainer
aea add connection fetchai/oef:0.2.0
aea add skill fetchai/ml_train:0.1.0
aea install
aea config set agent.default_connection fetchai/oef:0.2.0
```
``` bash
aea fetch fetchai/ml_model_trainer:0.2.0
cd ml_model_trainer
```
``` bash
aea install
```
``` bash
aea run --connections fetchai/oef:0.2.0
```
``` bash
aea create ml_data_provider
cd ml_data_provider
aea add connection fetchai/oef:0.2.0
aea add skill fetchai/ml_data_provider:0.1.0
aea install
aea config set agent.default_connection fetchai/oef:0.2.0
```
``` bash
aea create ml_model_trainer
cd ml_model_trainer
aea add connection fetchai/oef:0.2.0
aea add skill fetchai/ml_train:0.1.0
aea install
aea config set agent.default_connection fetchai/oef:0.2.0
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
aea config set vendor.fetchai.skills.ml_data_provider.models.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.ml_data_provider.models.strategy.args.ledger_id ethereum
```
``` bash
aea config set vendor.fetchai.skills.ml_train.models.strategy.args.max_buyer_tx_fee 10000 --type int
aea config set vendor.fetchai.skills.ml_train.models.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.ml_train.models.strategy.args.ledger_id ethereum
```
``` bash
aea run --connections fetchai/oef:0.2.0
```
``` bash
cd ..
aea delete ml_data_provider
aea delete ml_model_trainer
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
|      price_per_data_batch: 100    |      price_per_data_batch: 100   |
|      batch_size: 2                |      batch_size: 2               |
|      seller_tx_fee: 0             |      seller_tx_fee: 0            |
|      buyer_tx_fee: 10             |      buyer_tx_fee: 10            |
|      dataset_id: 'fmnist'         |      dataset_id: 'fmnist'        |
|      currency_id: 'FET'           |      currency_id: 'ETH'          |
|      ledger_id: 'fetchai'         |      ledger_id: 'ethereum'       |
|      is_ledger_tx: True           |      is_ledger_tx: True          |
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
|      dataset_id: 'fmnist'         |      dataset_id: 'fmnist'        |
|      max_unit_price: 70           |      max_unit_price: 70          |
|      max_buyer_tx_fee: 20         |      max_buyer_tx_fee: 20        |
|      currency_id: 'FET'           |      currency_id: 'ETH'          |
|      ledger_id: 'fetchai'         |      ledger_id: 'ethereum'       |
|      is_ledger_tx: True           |      is_ledger_tx: True          |
|----------------------------------------------------------------------| 
```

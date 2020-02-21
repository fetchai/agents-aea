``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

``` bash
aea create my_thermometer_aea
cd my_thermometer_aea
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/thermometer:0.1.0
aea install
```

``` bash
aea create my_thermometer_client
cd my_thermometer_client
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/thermometer_client:0.1.0
aea install
```

```bash
aea generate-key fetchai
aea add-key fetchai fet_private_key.txt
```

```bash
aea generate-key ethereum
aea add-key ethereum eth_private_key.txt
```

``` bash
aea generate-wealth fetchai
```

``` bash
aea generate-wealth ethereum
```

``` yaml
|----------------------------------------------------------------------|
|         FETCHAI                   |           ETHEREUM               |
|-----------------------------------|----------------------------------|
|models:                            |models:                           |              
|  strategy:                        |  strategy:                       |
|     class_name: Strategy          |     class_name: Strategy         |
|    args:                          |    args:                         |
|      price_per_row: 1             |      price_per_row: 1            |
|      seller_tx_fee: 0             |      seller_tx_fee: 0            |
|      currency_id: 'FET'           |      currency_id: 'ETH'          |
|      ledger_id: 'fetchai'         |      ledger_id: 'ethereum'       |
|      has_sensor: True             |      has_sensor: True            |
|      is_ledger_tx: True           |      is_ledger_tx: True          |
|----------------------------------------------------------------------| 
```

``` bash
aea config set vendor.fetchai.skills.thermometer.models.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.thermometer.models.strategy.args.ledger_id ethereum
```

``` yaml
|----------------------------------------------------------------------|
|         FETCHAI                   |           ETHEREUM               |
|-----------------------------------|----------------------------------|
|models:                            |models:                           |              
|  strategy:                        |  strategy:                       |
|     class_name: Strategy          |     class_name: Strategy         |
|    args:                          |    args:                         |
|      max_price: 4                 |      max_price: 40               |
|      max_buyer_tx_fee: 1          |      max_buyer_tx_fee: 200000    |
|      currency_id: 'FET'           |      currency_id: 'ETH'          |
|      ledger_id: 'fetchai'         |      ledger_id: 'ethereum'       |
|      is_ledger_tx: True           |      is_ledger_tx: True          |
|ledgers: ['fetchai']               |ledgers: ['ethereum']             |
|----------------------------------------------------------------------| 
```

``` bash
aea config set vendor.fetchai.skills.thermometer_client.models.strategy.args.max_buyer_tx_fee 10000 --type int
aea config set vendor.fetchai.skills.thermometer_client.models.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.thermometer_client.models.strategy.args.ledger_id ethereum
```

``` yaml
addr: ${OEF_ADDR: 127.0.0.1}
```

```bash 
aea add connection fetchai/oef:0.1.0
aea install
aea run --connections fetchai/oef:0.1.0
```

```bash 
cd ..
aea delete my_thermometer_aea
aea delete my_thermometer_client
```

``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

``` bash
aea create my_weather_station
```

``` bash
cd my_weather_station
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/weather_station:0.1.0
aea install
```

``` bash
aea config set vendor.fetchai.skills.weather_station.models.strategy.args.is_ledger_tx False --type bool
```

``` bash
aea run --connections fetchai/oef:0.1.0
```

``` bash
aea create my_weather_client
```

``` bash
cd my_weather_client
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/weather_client:0.1.0
aea install
```

```
aea config set vendor.fetchai.skills.weather_client.models.strategy.args.is_ledger_tx False --type bool
```

``` bash
aea run --connections fetchai/oef:0.1.0
```

``` bash
cd ..
aea delete my_weather_station
aea delete my_weather_client
```

``` bash
aea create my_weather_station
cd my_weather_station
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/weather_station:0.1.0
aea install
```

``` bash
aea create my_weather_client
cd my_weather_client
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/weather_client:0.1.0
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
|      date_one: "1/10/2019"        |      date_one: "1/10/2019"       |
|      date_two: "1/12/2019"        |      date_two: "1/12/2019"       |
|      price_per_row: 1             |      price_per_row: 1            |
|      seller_tx_fee: 0             |      seller_tx_fee: 0            |
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
|      max_price: 4                 |      max_price: 40               |
|      max_buyer_tx_fee: 1          |      max_buyer_tx_fee: 200000    |
|      currency_id: 'FET'           |      currency_id: 'ETH'          |
|      ledger_id: 'fetchai'         |      ledger_id: 'ethereum'       |
|      is_ledger_tx: True           |      is_ledger_tx: True          |
|ledgers: ['fetchai']               |ledgers: ['ethereum']             |
|----------------------------------------------------------------------| 
```

``` bash
aea config set vendor.fetchai.skills.weather_client.models.strategy.args.max_buyer_tx_fee 10000 --type int
aea config set vendor.fetchai.skills.weather_client.models.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.weather_client.models.strategy.args.ledger_id ethereum
aea config set vendor.fetchai.skills.weather_client.models.strategy.args.is_ledger_tx True --type bool
```

``` bash
aea run --connections fetchai/oef:0.1.0
```

``` bash
cd ..
aea delete my_weather_station
aea delete my_weather_client
```

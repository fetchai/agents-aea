``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```
``` bash
aea fetch fetchai/weather_station:0.8.0 --alias my_weather_station
cd my_weather_station
aea install
```
``` bash
aea create my_weather_station
cd my_weather_station
aea add connection fetchai/oef:0.6.0
aea add connection fetchai/ledger:0.2.0
aea add skill fetchai/weather_station:0.6.0
aea install
aea config set agent.default_connection fetchai/oef:0.6.0
```
``` bash
aea fetch fetchai/weather_client:0.8.0 --alias my_weather_client
cd my_weather_client
aea install
```
``` bash
aea create my_weather_client
cd my_weather_client
aea add connection fetchai/oef:0.6.0
aea add connection fetchai/ledger:0.2.0
aea add skill fetchai/weather_client:0.5.0
aea install
aea config set agent.default_connection fetchai/oef:0.6.0
```
``` bash
aea generate-key fetchai
aea add-key fetchai fet_private_key.txt
```
``` bash
aea generate-wealth fetchai
```
``` bash
aea generate-key ethereum
aea add-key ethereum eth_private_key.txt
```
``` bash
aea generate-wealth ethereum
```
``` bash
aea generate-key cosmos
aea add-key cosmos cosmos_private_key.txt
```
``` bash
aea generate-wealth cosmos
```
``` bash
aea config set vendor.fetchai.skills.weather_station.models.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.weather_station.models.strategy.args.ledger_id ethereum
```
``` bash
aea config set vendor.fetchai.skills.weather_station.models.strategy.args.currency_id ATOM
aea config set vendor.fetchai.skills.weather_station.models.strategy.args.ledger_id cosmos
```
``` bash
aea config set vendor.fetchai.skills.weather_client.models.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.weather_client.models.strategy.args.ledger_id ethereum
```
``` bash
aea config set vendor.fetchai.skills.weather_client.models.strategy.args.currency_id ATOM
aea config set vendor.fetchai.skills.weather_client.models.strategy.args.ledger_id cosmos
```
``` bash
aea run
```
``` bash
cd ..
aea delete my_weather_station
aea delete my_weather_client
```
``` yaml
default_routing:
  fetchai/ledger_api:0.1.0: fetchai/ledger:0.2.0
```
``` yaml
default_routing:
  fetchai/ledger_api:0.1.0: fetchai/ledger:0.2.0
```

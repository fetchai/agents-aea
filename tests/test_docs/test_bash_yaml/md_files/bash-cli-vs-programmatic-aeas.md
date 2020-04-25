``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```
``` bash
aea config set vendor.fetchai.skills.weather_station.models.strategy.args.is_ledger_tx False --type bool
```
``` bash
aea run --connections fetchai/oef:0.2.0
```
``` bash
python weather_client.py
```

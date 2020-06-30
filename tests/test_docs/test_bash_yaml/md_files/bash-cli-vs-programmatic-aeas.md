``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```
``` bash
aea fetch fetchai/weather_station:0.5.0
cd weather_station
```
``` bash
aea config set vendor.fetchai.skills.weather_station.models.strategy.args.is_ledger_tx False --type bool
```
``` bash
aea run
```
``` bash
python weather_client.py
```

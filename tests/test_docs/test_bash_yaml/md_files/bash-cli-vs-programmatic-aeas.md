``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```
``` bash
svn export https://github.com/fetchai/agents-aea.git/trunk/packages
```
``` bash
aea fetch fetchai/weather_station:0.8.0
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

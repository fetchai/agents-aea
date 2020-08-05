``` bash
svn export https://github.com/fetchai/agents-aea.git/trunk/packages
```
``` bash
aea fetch fetchai/weather_station:0.9.0
cd weather_station
```
``` bash
aea config set vendor.fetchai.skills.weather_station.models.strategy.args.is_ledger_tx False --type bool
```
``` bash
aea generate-key cosmos
aea add-key cosmos cosmos_private_key.txt
aea add-key cosmos cosmos_private_key.txt --connection
```
``` bash
aea run
```
``` bash
python weather_client.py
```

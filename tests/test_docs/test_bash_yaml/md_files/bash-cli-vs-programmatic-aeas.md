``` bash
svn export https://github.com/fetchai/agents-aea.git/trunk/packages
```
``` bash
aea fetch fetchai/weather_station:0.19.0
cd weather_station
```
``` bash
aea config set vendor.fetchai.skills.weather_station.models.strategy.args.is_ledger_tx False --type bool
```
``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
aea add-key fetchai fetchai_private_key.txt --connection
```
``` bash
aea run
```
``` bash
python weather_client.py
```

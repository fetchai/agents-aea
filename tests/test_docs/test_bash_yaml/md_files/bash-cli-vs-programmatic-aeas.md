``` bash
svn export https://github.com/fetchai/agents-aea.git/trunk/packages
```
```bash
pip install aea-ledger-fetchai
```
``` bash
aea fetch fetchai/weather_station:0.31.0
cd weather_station
aea install
aea build
```
``` bash
aea config set vendor.fetchai.skills.weather_station.models.strategy.args.is_ledger_tx False --type bool
```
``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
```
``` bash
aea generate-key fetchai fetchai_connection_private_key.txt
aea add-key fetchai fetchai_connection_private_key.txt --connection
```
``` bash
aea issue-certificates
```
``` bash
aea run
```
``` bash
python weather_client.py
```

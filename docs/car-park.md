# Car Park Agent Application

The Fetch.ai car park agent demo is documented in its own repo [here](https://github.com/fetchai/carpark_agent).


## To test the AEA functionality (without the detection)

First, create the carpark detection agent:
```
aea create car_detector
cd car_detector
aea add skill carpark_detection
aea install
```

Then, create the carpark client agent:
```
aea create car_data_buyer
cd car_data_buyer
aea add skill carpark_client
aea install
aea generate-key fetchai
aea add-key fetchai fet_private_key.txt
```

Add the ledger info to both aea configs:
```
ledger_apis:
  - ledger_api:
      ledger: fetchai
      addr: alpha.fetch-ai.com
      port: 80
```

Fund the carpark client agent:
```
cd ..
python scripts/fetchai_wealth_generation.py --private-key car_data_buyer/fet_private_key.txt --amount 10000000000 --addr alpha.fetch-ai.com --port 80
```

Then, in the carpark detection skill settings (`car_detector/skills/carpark_detection/skill.yaml`) of the detection agent comment out database related settings:
```
# db_is_rel_to_cwd: true
# db_rel_dir: ../temp_files
```

Then, in the carpark client skill settings (`car_data_buyer/skills/carpark_client/skill.yaml`) of the client agent do:
```
max_detection_age: 36000000
```

Then, launch an OEF node instance:
```
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

Finally, run both agents with `aea run`.

You can see that the agents find each other, negotiate and eventually trade.

When you're finished, delete your agents:
```
cd ..
aea delete car_detector
aea delete car_data_buyer
```
<br />

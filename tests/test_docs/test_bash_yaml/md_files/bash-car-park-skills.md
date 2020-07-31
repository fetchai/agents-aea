``` bash
aea fetch fetchai/car_detector:0.9.0
cd car_detector
aea install
```
``` bash
aea create car_detector
cd car_detector
aea add connection fetchai/p2p_libp2p:0.6.0
aea add connection fetchai/soef:0.6.0
aea add connection fetchai/ledger:0.2.0
aea add skill fetchai/carpark_detection:0.7.0
aea install
aea config set agent.default_connection fetchai/p2p_libp2p:0.6.0
```
``` bash
aea fetch fetchai/car_data_buyer:0.9.0
cd car_data_buyer
aea install
```
``` bash
aea create car_data_buyer
cd car_data_buyer
aea add connection fetchai/p2p_libp2p:0.6.0
aea add connection fetchai/soef:0.6.0
aea add connection fetchai/ledger:0.2.0
aea add skill fetchai/carpark_client:0.7.0
aea install
aea config set agent.default_connection fetchai/p2p_libp2p:0.6.0
```
``` bash
aea generate-key cosmos
aea add-key cosmos cosmos_private_key.txt
aea add-key cosmos cosmos_private_key.txt --connection
```
``` bash
aea generate-key cosmos
aea add-key cosmos cosmos_private_key.txt
aea add-key cosmos cosmos_private_key.txt --connection
```
``` bash
aea generate-wealth cosmos
```
``` bash
aea run
```
``` bash
aea run
```
``` bash
cd ..
aea delete car_detector
aea delete car_data_buyer
```
``` yaml
default_routing:
  fetchai/ledger_api:0.2.0: fetchai/ledger:0.2.0
  fetchai/oef_search:0.3.0: fetchai/soef:0.6.0
```
``` yaml
default_routing:
  fetchai/ledger_api:0.2.0: fetchai/ledger:0.2.0
  fetchai/oef_search:0.3.0: fetchai/soef:0.6.0
```
``` yaml
config:
  delegate_uri: 127.0.0.1:11001
  entry_peers: ['SOME_ADDRESS']
  local_uri: 127.0.0.1:9001
  log_file: libp2p_node.log
  public_uri: 127.0.0.1:9001
```
